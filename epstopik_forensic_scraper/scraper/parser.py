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
    """Extract data rows from a table element, skipping header rows."""
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr")
    else:
        rows = table.find_all("tr")

    # Filter out header rows (contain <th>)
    return [r for r in rows if r.find("td") and not r.find("th")]


def _parse_row(row: Tag, index: int, page_num: int) -> WorkbookItem:
    """Parse a single table row into a WorkbookItem."""
    cells = row.find_all("td")
    item = WorkbookItem(
        row_index=index,
        title=f"Row {index}",
        page_num=page_num,
    )

    # Title cell
    title_cell = cells[C.TITLE_CELL_INDEX] if len(cells) > C.TITLE_CELL_INDEX else None
    if title_cell:
        link = title_cell.select_one(C.TITLE_LINK_SELECTOR) if C.TITLE_LINK_SELECTOR else None
        if link:
            item.title = link.get_text(strip=True) or title_cell.get_text(strip=True)

            # Extract detail URL or JS call
            href = link.get("href", "")
            onclick = link.get("onclick", "")
            if href and href.startswith("javascript:"):
                item.detail_js = href
            elif href and href not in ("#", ""):
                item.detail_url = href
            if onclick:
                m = re.search(C.DETAIL_JS_PATTERN, onclick)
                if m:
                    item.detail_js = f"fn_select_cm('{m.group(1)}')"
                    item.detail_url = (
                        f"/epstopik/book/pub/publicWorkBookCmList.do"
                        f"?lang=en&tmp_revCd={m.group(1)}"
                    )
        else:
            item.title = title_cell.get_text(strip=True)

    # Extract download links from entire row
    for a in row.find_all("a", href=True):
        href = a["href"]
        if ".hwp" in href.lower():
            item.hwp_urls.append(href)
        elif ".pdf" in href.lower():
            item.pdf_urls.append(href)
        elif ".zip" in href.lower():
            item.audio_zip_url = href

    # Date cell
    if len(cells) > C.DATE_CELL_INDEX:
        date_text = cells[C.DATE_CELL_INDEX].get_text(strip=True)
        if date_text:
            item.published_date = date_text

    # View count cell
    if len(cells) > C.VIEW_CELL_INDEX:
        view_text = cells[C.VIEW_CELL_INDEX].get_text(strip=True)
        if view_text:
            item.view_count = view_text

    # Fallback: use onclick for detail JS
    if not item.detail_url and not item.detail_js:
        for td in cells:
            onclick = td.get("onclick", "")
            m = re.search(C.DETAIL_JS_PATTERN, onclick)
            if m:
                item.detail_js = f"fn_select_cm('{m.group(1)}')"
                break

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
