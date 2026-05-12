# EPS-TOPIK Forensic Scraper

Forensic-grade web scraper for EPS-TOPIK open test workbooks with **full audit trail**, **data provenance**, and **integrity verification**.

## Architecture

```
                     ┌─────────────┐
                     │   Typer CLI  │
                     └──────┬──────┘
                            │
              ┌─────────────┼──────────────┐
              │             │              │
         ┌────▼────┐  ┌────▼────┐  ┌─────▼─────┐
         │ Fetcher │  │ Parser  │  │ Downloader │
         │ (httpx  │  │ (bs4 +  │  │ (stream +  │
         │ └→ pw)  │  │  lxml)  │  │  SHA256)   │
         └─────────┘  └─────────┘  └───────────┘
              │             │              │
              └─────────────┼──────────────┘
                            │
                     ┌──────▼──────┐
                     │  Forensics  │
                     │ (screenshot │
                     │  raw dump,  │
                     │  checksum)  │
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │  Provenance │
                     │  DB (SQLite)│
                     └─────────────┘
```

## Installation

```bash
pip install -e ".[playwright]"
playwright install chromium
```

## Usage

```bash
# Scrape all pages
epstopik scrape --max-pages 0

# Verify downloaded file integrity
epstopik verify

# Generate audit report
epstopik report
```

## Audit Trail

Every scraped artifact has:

| Layer | What | Proof |
|-------|------|-------|
| Raw HTML | `artifacts/raw_pages/{timestamp}_{page}.html` | SHA256 |
| Screenshot | `artifacts/screenshots/{timestamp}_{reason}.png` | Visual proof |
| Downloads | `artifacts/downloads/{sha256[:16]}_{filename}` | SHA256 in filename |
| Database | `provenance.db` via SQLModel | Full lineage + timestamps |

## Verification

```bash
sqlite3 artifacts/provenance.db
sqlite> .headers on
sqlite> SELECT * FROM downloadedfile;
```
