import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import settings
from db.database import init_db, get_session
from db.models import ScrapingJob, RawPage, ExtractedItem, DownloadedFile
from models.enums import ScrapeStatus
from models.schemas import WorkbookItem, FileAsset
from scraper.fetcher import HybridFetcher, UnrecoverableScrapeError
from scraper.parser import parse_workbook_list, parse_detail_page
from scraper.downloader import AssetDownloader, BaitAndSwitchError
from scraper import forensics as forensics_mod


class Orchestrator:
    def __init__(self):
        self.engine = init_db()
        self.fetcher = HybridFetcher()
        self.downloader = AssetDownloader()
        self._job_id: Optional[int] = None

    def run(self, start_page: int = 1, max_pages: int = 0):
        """Run the full scrape pipeline."""
        target_url = settings.BASE_URL + settings.LIST_PATH + "?lang=en"
        job = ScrapingJob(
            target_url=target_url,
            start_page=start_page,
            max_pages=max_pages,
            status=ScrapeStatus.RUNNING,
        )

        with get_session() as session:
            session.add(job)
            session.commit()
            self._job_id = job.id

        try:
            self._scrape_pages(start_page, max_pages)
            self._update_job_status(ScrapeStatus.SUCCESS)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self._update_job_status(ScrapeStatus.FAILED)
            raise
        finally:
            self.fetcher.close()
            self.downloader.close()

    def _scrape_pages(self, start_page: int, max_pages: int):
        """Scrape list pages and process items."""
        page = start_page
        consecutive_empty = 0

        while True:
            if max_pages > 0 and page > start_page + max_pages - 1:
                break
            # EPS-TOPIK is single-page (no pagination). Stop after page 1.
            if page > 1 and max_pages == 0:
                logger.info("Single-page site detected. Stopping after page 1.")
                break

            logger.info(f"--- Page {page} ---")
            try:
                html, method, screenshot_path = self.fetcher.fetch_list_page(page)
            except UnrecoverableScrapeError as e:
                logger.error(f"Cannot fetch page {page}: {e}")
                break

            # Save raw HTML
            page_url = self.fetcher._build_list_url(page)
            raw_path = forensics_mod.save_raw_page(html, page_url, page, self._job_id)
            html_sha256 = forensics_mod.compute_checksum(Path(raw_path))

            page_record = RawPage(
                job_id=self._job_id,
                url=page_url,
                page_num=page,
                fetch_method=method,
                raw_html_path=raw_path,
                html_sha256=html_sha256,
                screenshot_path=screenshot_path,
            )

            with get_session() as session:
                session.add(page_record)
                session.commit()
                page_id = page_record.id

            # Parse items
            items = parse_workbook_list(html, page)
            if not items:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    logger.info("Two consecutive pages empty; stopping.")
                    break
                # Take diagnostic screenshot
                forensics_mod.take_diagnostic_screenshot(
                    html_content=html,
                    reason=f"parse_fail_page{page}",
                )
            else:
                consecutive_empty = 0

            # Process each item
            for item in items:
                self._process_item(item, page_id)

            page += 1

    def _process_item(self, item: WorkbookItem, page_id: int):
        """Process a single workbook item: fetch detail, download files."""
        with get_session() as session:
            ext_item = ExtractedItem(
                job_id=self._job_id,
                page_id=page_id,
                row_index=item.row_index,
                title=item.title,
                published_date=item.published_date,
                detail_url=item.detail_url,
                detail_js=item.detail_js,
                pdf_urls=json.dumps(item.pdf_urls),
                hwp_urls=json.dumps(item.hwp_urls),
                audio_zip_url=item.audio_zip_url,
                view_count=item.view_count,
            )
            session.add(ext_item)
            session.commit()
            item_id = ext_item.id

        # Fetch detail page if available
        if item.detail_js and not item.detail_url:
            # Try to build URL from JS pattern
            detail_url = f"{settings.BASE_URL}{settings.CM_LIST_PATH}?lang=en&tmp_revCd={item.detail_js.split(chr(39))[1]}"
        elif item.detail_url:
            if item.detail_url.startswith("/"):
                detail_url = settings.BASE_URL + item.detail_url
            else:
                detail_url = item.detail_url
        else:
            detail_url = None

        if detail_url:
            try:
                html, _ = self.fetcher.fetch_detail_page(detail_url)
                item = parse_detail_page(html, item)
                # Update ExtractedItem with new URLs
                with get_session() as session:
                    ext = session.get(ExtractedItem, item_id)
                    if ext:
                        ext.hwp_urls = json.dumps(item.hwp_urls)
                        ext.pdf_urls = json.dumps(item.pdf_urls)
                        session.add(ext)
                        session.commit()
            except Exception as e:
                logger.warning(f"Detail fetch failed for {item.title}: {e}")

        # Download files
        all_urls = []
        for u in item.hwp_urls:
            all_urls.append((u, "hwp"))
        for u in item.pdf_urls:
            all_urls.append((u, "pdf"))
        if item.audio_zip_url:
            all_urls.append((item.audio_zip_url, "zip"))

        for url, url_type in all_urls:
            try:
                asset = self.downloader.download_file(url, url_type)
                self._save_file_asset(asset, item_id)
            except BaitAndSwitchError as e:
                logger.warning(f"Bait-and-switch for {url}: {e}")
            except Exception as e:
                logger.error(f"Download failed for {url}: {e}")

    def _save_file_asset(self, asset: FileAsset, item_id: int):
        with get_session() as session:
            record = DownloadedFile(
                item_id=item_id,
                source_url=asset.source_url,
                local_path=asset.local_path,
                file_sha256=asset.sha256,
                file_size=asset.size_bytes,
                mime_type=asset.mime_type.value,
            )
            session.add(record)
            session.commit()

    def _update_job_status(self, status: ScrapeStatus):
        with get_session() as session:
            job = session.get(ScrapingJob, self._job_id)
            if job:
                job.status = status.value
                job.ended_at = datetime.now()
                session.add(job)
                session.commit()

    def verify_integrity(self) -> list[dict]:
        """Verify downloaded files match their SHA256 stored in DB."""
        mismatches = []
        with get_session() as session:
            files = session.query(DownloadedFile).all()
            for f in files:
                path = Path(f.local_path)
                if not path.exists():
                    mismatches.append({
                        "id": f.id,
                        "expected_sha256": f.file_sha256,
                        "status": "FILE_MISSING",
                        "path": f.local_path,
                    })
                    continue
                actual = forensics_mod.compute_checksum(path)
                if actual != f.file_sha256:
                    mismatches.append({
                        "id": f.id,
                        "expected_sha256": f.file_sha256,
                        "actual_sha256": actual,
                        "status": "HASH_MISMATCH",
                        "path": f.local_path,
                    })
        return mismatches

    def generate_report(self) -> dict:
        """Generate audit manifest as JSON."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "artifacts_dir": str(settings.ARTIFACTS_DIR),
            "jobs": [],
        }
        with get_session() as session:
            jobs = session.query(ScrapingJob).all()
            for job in jobs:
                job_data = {
                    "id": job.id,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                    "target_url": job.target_url,
                    "status": job.status,
                    "pages": [],
                    "files": [],
                }
                # Pages
                for rp in job.raw_pages:
                    job_data["pages"].append({
                        "page_num": rp.page_num,
                        "url": rp.url,
                        "fetch_method": rp.fetch_method,
                        "raw_html_path": rp.raw_html_path,
                        "html_sha256": rp.html_sha256,
                        "screenshot_path": rp.screenshot_path,
                    })
                # Downloaded files
                for ext in job.extracted_items:
                    for df in ext.downloaded_files:
                        job_data["files"].append({
                            "url": df.source_url,
                            "local_path": df.local_path,
                            "sha256": df.file_sha256,
                            "size_bytes": df.file_size,
                            "mime_type": df.mime_type,
                        })
                report["jobs"].append(job_data)

        report_path = settings.ARTIFACTS_DIR / "audit_manifest.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Audit report saved: {report_path}")
        return report
