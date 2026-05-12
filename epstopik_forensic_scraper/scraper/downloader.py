import hashlib
import mimetypes
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from config.settings import settings
from models.schemas import FileAsset
from models.enums import MimeType


class DownloadError(Exception):
    pass


class BaitAndSwitchError(DownloadError):
    """URL claimed to be a file but returned HTML."""


class AssetDownloader:
    def __init__(self, client: Optional[httpx.Client] = None):
        self._client = client or httpx.Client(
            headers=settings.HEADERS,
            follow_redirects=True,
            timeout=60.0,
        )

    def download_file(self, url: str, url_type: str = "") -> FileAsset:
        """Download a file with SHA256 verification. Returns FileAsset."""
        if not url.startswith("http"):
            base = settings.BASE_URL.rstrip("/")
            url = base + url

        logger.info(f"Downloading: {url}")
        resp = self._client.get(url)
        resp.raise_for_status()

        content = resp.content
        sha256 = hashlib.sha256(content).hexdigest()
        mime_type = self._detect_mime(resp, url)

        # Detect bait-and-switch: expected file but got HTML
        if MimeType.HTML in mime_type and any(
            ext in url.lower() for ext in [".hwp", ".pdf", ".zip", ".mp3"]
        ):
            raise BaitAndSwitchError(
                f"URL {url} returned HTML instead of expected file. "
                f"Saving with .html extension for investigation."
            )

        # Determine filename
        ext = self._guess_extension(mime_type, url)
        local_dir = settings.ARTIFACTS_DIR / "downloads"
        local_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{sha256[:16]}_{Path(url).stem}{ext}"
        local_path = str(local_dir / filename)

        local_dir.mkdir(parents=True, exist_ok=True)
        Path(local_path).write_bytes(content)
        logger.info(f"Saved: {local_path} ({len(content)} bytes, sha256={sha256[:16]}...)")

        return FileAsset(
            source_url=url,
            local_path=local_path,
            sha256=sha256,
            size_bytes=len(content),
            mime_type=mime_type,
        )

    def _detect_mime(self, resp: httpx.Response, url: str) -> MimeType:
        """Detect MIME type from Content-Type header or magic bytes."""
        content_type = resp.headers.get("content-type", "").lower()
        if "pdf" in content_type:
            return MimeType.PDF
        if "hwp" in content_type or "hancom" in content_type:
            return MimeType.HWP
        if "zip" in content_type:
            return MimeType.ZIP
        if "mpeg" in content_type or "mp3" in content_type:
            return MimeType.MP3
        if "jpeg" in content_type or "jpg" in content_type:
            return MimeType.IMAGE_JPEG
        if "png" in content_type:
            return MimeType.IMAGE_PNG
        if "html" in content_type:
            return MimeType.HTML

        # Fallback: detect from URL extension
        ext = Path(url).suffix.lower()
        mime_map = {
            ".pdf": MimeType.PDF,
            ".hwp": MimeType.HWP,
            ".zip": MimeType.ZIP,
            ".mp3": MimeType.MP3,
        }
        return mime_map.get(ext, MimeType.OCTET)

    def _guess_extension(self, mime: MimeType, url: str) -> str:
        """Guess file extension from MIME type or URL."""
        ext_map = {
            MimeType.PDF: ".pdf",
            MimeType.HWP: ".hwp",
            MimeType.ZIP: ".zip",
            MimeType.MP3: ".mp3",
            MimeType.HTML: ".html",
        }
        return ext_map.get(mime, Path(url).suffix or ".bin")

    def close(self):
        if self._client:
            self._client.close()
