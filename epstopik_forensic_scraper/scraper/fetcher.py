import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from config.settings import settings
from models.enums import FetchMethod


class FetcherError(Exception):
    pass


class UnrecoverableScrapeError(FetcherError):
    pass


class HybridFetcher:
    def __init__(self):
        self._client: Optional[httpx.Client] = None
        self._playwright_available = False
        self._check_playwright()

    def _check_playwright(self):
        try:
            import playwright  # noqa: F401
            self._playwright_available = True
        except ImportError:
            logger.warning("playwright not installed; run: pip install '.[playwright]' && playwright install chromium")

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                headers=settings.HEADERS,
                follow_redirects=True,
                timeout=30.0,
            )
            # Prime the session by visiting the main page
            self._client.get(settings.BASE_URL + "/epstopik/home/main/mainPage.do?lang=en")
        return self._client

    def fetch_list_page(
        self,
        page_num: int = 1,
        method: str = "auto",
    ) -> tuple[str, str, str]:
        """Fetch a list page. Returns (html, fetch_method, screenshot_path)."""
        url = self._build_list_url(page_num)
        fetch_method = FetchMethod.HTTPX
        screenshot_path = ""

        if method in ("auto", "httpx"):
            try:
                html = self._fetch_httpx(url)
                # Quick validation: look for table elements
                if self._validate_html(html):
                    return html, fetch_method.value, screenshot_path
                logger.warning(f"httpx response for page {page_num} lacks table content; falling back to playwright")
            except Exception as e:
                logger.warning(f"httpx failed for page {page_num}: {e}")

        # Fallback to Playwright
        if method in ("auto", "playwright") and self._playwright_available:
            fetch_method = FetchMethod.PLAYWRIGHT
            html, screenshot_path = self._fetch_playwright(url)
            return html, fetch_method.value, screenshot_path

        raise UnrecoverableScrapeError(
            f"All fetch methods exhausted for page {page_num}. "
            "Install playwright or check network connectivity."
        )

    def fetch_detail_page(self, url: str) -> tuple[str, str]:
        """Fetch a detail/CM list page."""
        try:
            html = self._fetch_httpx(url)
            return html, FetchMethod.HTTPX.value
        except Exception:
            if self._playwright_available:
                html, _ = self._fetch_playwright(url)
                return html, FetchMethod.PLAYWRIGHT.value
            raise

    def _build_list_url(self, page_num: int) -> str:
        return (
            f"{settings.BASE_URL}{settings.LIST_PATH}"
            f"?lang={settings.DEFAULT_LANG}&pageIndex={page_num}"
        )

    def _build_post_payload(self, page_num: int) -> dict:
        # TODO(inspect): Check network tab — some Spring MVC sites require POST
        return {
            "lang": settings.DEFAULT_LANG,
            "pageIndex": str(page_num),
            "searchCondition": "0",
            "searchKeyword": "",
        }

    def _fetch_httpx(self, url: str) -> str:
        time.sleep(settings.REQUEST_DELAY)
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp.text

    def _post_paginate(self, page_num: int) -> str:
        """POST-based pagination for Spring MVC."""
        time.sleep(settings.REQUEST_DELAY)
        url = settings.BASE_URL + settings.LIST_PATH
        payload = self._build_post_payload(page_num)
        resp = self.client.post(url, data=payload)
        resp.raise_for_status()
        return resp.text

    def _validate_html(self, html: str) -> bool:
        """Quick heuristic: does the HTML contain a table or list structure?"""
        indicators = ["<table", "class=\"tableType\"", "class=\"list\"", "tbody", "<th"]
        return any(ind in html.lower() for ind in indicators)

    def _fetch_playwright(self, url: str) -> tuple[str, str]:
        """Render page with Playwright, return (html, screenshot_path)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=settings.HEADERS["User-Agent"],
                locale="ko-KR",
            )
            page = context.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                # Wait for table to load
                # TODO(inspect): adjust selector to match actual table
                page.wait_for_selector("table", timeout=10000)
                html = page.content()

                # Screenshot for forensics
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_dir = settings.ARTIFACTS_DIR / "screenshots"
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = str(screenshot_dir / f"pw_fallback_{ts}.png")
                page.screenshot(path=screenshot_path, full_page=True)

                return html, screenshot_path
            finally:
                browser.close()

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
