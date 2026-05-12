"""
CSS selectors and form field names for EPS-TOPIK workbook list page.

TODO(inspect): Open https://epstopik.hrdkorea.or.kr/epstopik/book/pub/publicWorkBookList.do?lang=en
in browser DevTools and update these selectors to match the actual DOM structure.
"""

# ── List Page ──
# The workbook list table — look for <table> with class containing "list" or "tbl"
LIST_TABLE_SELECTOR = "table.tableType, table.list, table.tb_list, table[summary*='목록']"

# Row selector within the table body
ROW_SELECTOR = "table.tableType tbody tr, table.list tbody tr"

# Cell extractors (relative to each row)
TITLE_CELL_INDEX = 1  # 0-based column index for title
TITLE_LINK_SELECTOR = "a"  # <a> inside the title cell

# Date cell (if present)
DATE_CELL_INDEX = 2

# View count cell
VIEW_CELL_INDEX = 3

# Fallback: find all links containing download patterns
DOWNLOAD_LINK_PATTERN = "fnFileDown|fnDownload|download|Down"

# JavaScript function patterns in onclick
DETAIL_JS_PATTERN = r"fn_select_cm\('(\d+)'\)"

# ── Detail / CM List Page ──
CM_TABLE_SELECTOR = "table.tableType, table.list"
CM_DOWNLOAD_LINK_SELECTOR = "a[href*='.hwp'], a[href*='.pdf'], a[href*='.zip']"

# ── Pagination ──
# Form name for the list page
LIST_FORM_NAME = "listForm"  # TODO(inspect): verify in DevTools
# Page index field name (Spring MVC convention)
PAGE_FIELD_NAME = "pageIndex"  # TODO(inspect): verify in DevTools

# ── Special set ──
SPECIAL_REV_CD = "3"  # revCd for special EPS-TOPIK questions
