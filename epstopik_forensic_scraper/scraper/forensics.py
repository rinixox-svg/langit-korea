import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import settings


def save_raw_page(
    html: str,
    url: str,
    page_num: int,
    job_id: int,
) -> str:
    """Save raw HTML content to disk. Returns file path."""
    html_bytes = html.encode("utf-8")
    sha256 = hashlib.sha256(html_bytes).hexdigest()

    raw_dir = settings.ARTIFACTS_DIR / "raw_pages"
    raw_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_p{page_num:03d}_{sha256[:12]}.html"
    filepath = raw_dir / filename

    filepath.write_bytes(html_bytes)
    logger.info(f"Raw page saved: {filepath} ({len(html_bytes)} bytes, sha256={sha256[:16]}...)")
    return str(filepath)


def take_diagnostic_screenshot(
    html_content: Optional[str] = None,
    url: Optional[str] = None,
    reason: str = "diagnostic",
) -> Optional[str]:
    """Take a screenshot for forensic audit.
    If html_content is provided, render it locally.
    Otherwise, navigate to url and screenshot.
    """
    screenshot_dir = settings.ARTIFACTS_DIR / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_reason = "".join(c for c in reason if c.isalnum() or c in " _-")[:40]
    filename = f"{ts}_{safe_reason}.png"
    filepath = screenshot_dir / filename

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("playwright not installed; cannot take screenshot")
        return None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            if html_content:
                page.set_content(html_content, wait_until="networkidle")
            elif url:
                page.goto(url, wait_until="networkidle", timeout=30000)
            else:
                return None

            page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        finally:
            browser.close()


def compute_checksum(filepath: Path) -> str:
    """Compute SHA256 of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()
