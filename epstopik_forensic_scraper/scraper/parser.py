import re
from typing import Optional

from bs4 import BeautifulSoup, Tag
from loguru import logger

from models.schemas import WorkbookItem, PageSnapshot
from . import constants as C


class ParseError(Exception):
    pass


class SelectorMismatchError(ParseError):
    pass


def parse_workbook_list(html: str, page_num: int = 1) -> list[WorkbookItem]:
    """Parse workbook list page HTML into structured items."""
    soup = BeautifulSoup(html, "lxml")
    items: list[WorkbookItem] = []

    # Strategy 1: Use configured table selector
    table = soup.select_one(C.LIST_TABLE_SELECTOR)
    if table:
        rows = _extract_rows_from_table(table)
        if rows:
            items = [_parse_row(r, i, page_num) for i, r in enumerate(rows)]
            if any(it.title for it in items):
                logger.info(f"Parsed {len(items)} items from table (page {page_num})")
                return items

    # Strategy 2: Find any table with multiple rows
    for tbl in soup.find_all("table"):
        rows = _extract_rows_from_table(tbl)
        if len(rows) >= 2:
            candidates = [_parse_row(r, i, page_num) for i, r in enumerate(rows)]
            if any(c.title for c in candidates):
                logger.info(f"Parsed {len(candidates)} items from fallback table (page {page_num})")
                return candidates

    # Strategy 3: Find download links directly
    items = _fallback_parse_links(soup, page_num)
    if items:
        logger.info(f"Parsed {len(items)} items via link fallback (page {page_num})")
        return items

    logger.warning(f"No items found on page {page_num}")
    return []


def _extract_rows_from_table(table: Tag) -> list[Tag]:
    """Extract data rows from a table element.

    EPS-TOPIK table uses rowspan for category grouping:
    - Row 1: <td rowspan=3> for category spanning multiple sub-rows
    - Data rows contain <td> with download links
    - Header rows contain <th>
    """
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr")
    else:
        rows = table.find_all("tr")

    # Filter: keep rows with <td> that contain <a> links (data rows)
    data_rows = []
    for r in rows:
        tds = r.find_all("td")
        has_links = any(td.find("a", href=True) for td in tds)
        if tds and has_links:
            data_rows.append(r)

    return data_rows if data_rows else [r for r in rows if r.find("td") and not r.find("th")]


def _parse_row(row: Tag, index: int, page_num: int) -> WorkbookItem:
    """Parse a single table row into a WorkbookItem.

    EPS-TOPIK row structure:
    - Row may have <td rowspan=N> for category (no. column)
    - Content TDs have download <a> links
    """
    cells = row.find_all("td")
    item = WorkbookItem(
        row_index=index,
        title=f"Row {index}",
        page_num=page_num,
    )

    # Extract category/title from the first TDs
    for td in cells[:2]:
        txt = td.get_text(strip=True)
        if txt and len(txt) > 1:
            item.title = txt
            break

    # Extract ALL download links from this row
    for a in row.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)

        # Check for JavaScript-based navigation
        onclick = a.get("onclick", "")
        m = re.search(C.DETAIL_JS_PATTERN, onclick or href)
        if m:
            item.detail_js = f"fn_select_cm('{m.group(1)}')"
            item.detail_url = (
                f"/epstopik/book/pub/publicWorkBookCmList.do"
                f"?lang=en&tmp_revCd={m.group(1)}"
            )

        # Categorize by file extension
        if ".hwp" in href.lower():
            if href not in item.hwp_urls:
                item.hwp_urls.append(href)
        elif ".pdf" in href.lower():
            if href not in item.pdf_urls:
                item.pdf_urls.append(href)
        elif ".zip" in href.lower():
            item.audio_zip_url = href

    # View count
    if len(cells) > 2:
        view_text = cells[-1].get_text(strip=True)
        if view_text and view_text.isdigit():
            item.view_count = view_text

    return item


def _fallback_parse_links(soup: BeautifulSoup, page_num: int) -> list[WorkbookItem]:
    """Fallback: find all download links and create items."""
    items: list[WorkbookItem] = []
    seen_urls: set[str] = set()

    for i, a in enumerate(soup.find_all("a", href=True)):
        href = a["href"]
        text = a.get_text(strip=True)

        is_download = any(
            ext in href.lower()
            for ext in [".hwp", ".pdf", ".zip", "download", "filedown"]
        )
        if not is_download and not text:
            continue

        if href in seen_urls:
            continue
        seen_urls.add(href)

        item = WorkbookItem(
            row_index=i,
            title=text or f"Download {i}",
            page_num=page_num,
        )
        if ".hwp" in href.lower():
            item.hwp_urls.append(href)
        elif ".pdf" in href.lower():
            item.pdf_urls.append(href)
        elif ".zip" in href.lower():
            item.audio_zip_url = href
        else:
            item.detail_url = href

        items.append(item)

    return items


def parse_detail_page(html: str, parent_item: WorkbookItem) -> WorkbookItem:
    """Parse a detail/CM list page for additional download links."""
    soup = BeautifulSoup(html, "lxml")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".hwp" in href.lower() and href not in parent_item.hwp_urls:
            parent_item.hwp_urls.append(href)
        elif ".pdf" in href.lower() and href not in parent_item.pdf_urls:
            parent_item.pdf_urls.append(href)
        elif ".zip" in href.lower() and not parent_item.audio_zip_url:
            parent_item.audio_zip_url = href

    return parent_item
