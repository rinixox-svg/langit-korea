"""
CSS selectors and form field names — verified against live page.
"""

# ── List Page ──
# Main table containing workbook list
LIST_TABLE_SELECTOR = "table.tableType"

# Look for rows that have <td> elements (data rows)
ROW_SELECTOR = "table.tableType tr"

# Data rows have <td> inside. First row with rowspan is a category header.
# Content rows have download links in TD[1] or TD[2].
TITLE_CELL_INDEX = 0  # 0-based: first TD has the category or row number
TITLE_LINK_SELECTOR = "a[href*='.hwp'], a[href*='.zip']"
# Download links are text like "Download1", "Download2"
DOWNLOAD_LINK_SELECTOR = "a[href]"

# JavaScript function for detail page navigation
DETAIL_JS_PATTERN = r"fn_select_cm\('(\d+)'\)"

# ── Detail / CM List Page ──
CM_TABLE_SELECTOR = "table.tableType"
CM_DOWNLOAD_LINK_SELECTOR = "a[href*='.hwp'], a[href*='.pdf'], a[href*='.zip']"

# ── Pagination ──
# One-page site — no pagination needed.
# Form fields for POST-based navigation (if needed)
LIST_FORM_NAME = "listForm"
PAGE_FIELD_NAME = "pageIndex"
CM_REV_CD_FIELD = "tmp_revCd"
LANG_FIELD = "lang"

# ── Special set ──
SPECIAL_REV_CD = "3"

# ── Parsing hints ──
# The table has rows like:
# Row 1 (rowspan=3): [no.=1] [구성=Reading] [문제+정답 links] [___]
# Row 2: [___] [듣기/Listening] [문제+정답 links] [___]
# Row 3: [___] [Voice file] [ZIP links] [___]
# Row 4 (header): [no.] [Title] [view]
# Row 5: [no.=3] [Special EPS-TOPIK] [view count]
