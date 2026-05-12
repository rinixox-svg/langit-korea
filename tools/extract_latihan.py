import os
import fitz
import requests
import json
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

SEKSI_MAP = {
    0: 'vocab1', 1: 'grammar1', 2: 'conversation1',
    3: 'vocab2', 4: 'grammar2', 5: 'conversation2',
    6: 'budaya',
}

SECTIONS = [
    ('vocab1', 1), ('grammar1', 2), ('conversation1', 3),
    ('vocab2', 4), ('grammar2', 5), ('conversation2', 6),
    ('budaya', 7),
]

def extract_text(doc, page_num):
    if page_num < len(doc):
        return doc.load_page(page_num).get_text().strip()
    return ""

def parse_lines(text):
    if not text:
        return []
    items = []
    for line in text.split('\n'):
        line = line.strip()
        if line and len(line) > 1:
            items.append(line)
    return items

def make_records(unit_num, pages):
    records = []
    order = 0
    for seksi, pg in SECTIONS:
        if pg > len(pages):
            continue
        text = pages[pg - 1]
        if not text:
            continue
        order += 1
        rec = {
            "unit": unit_num,
            "seksi": seksi,
            "tipe_latihan": "flashcard",
            "urutan": order,
            "teks_korea": text[:2000],
            "akses": "free",
        }
        records.append(rec)
    return records

def upload(records):
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    url = f"{SUPABASE_URL}/rest/v1/latihan_interaktif"
    ok = 0
    for rec in records:
        r = requests.post(url, headers=headers, json=rec, timeout=30)
        if r.status_code in (200, 201):
            ok += 1
        else:
            print(f"  FAIL unit={rec['unit']} seksi={rec['seksi']}: {r.status_code}")
    return ok

def main():
    src = Path("assets/langit-korea-modules")
    if not src.exists():
        print(f"Not found: {src}")
        return
    total = 0
    for n in range(31, 61):
        files = list(src.glob(f"unit_{n}_*.pdf"))
        if not files:
            print(f"No PDF for unit {n}")
            continue
        doc = fitz.open(str(files[0]))
        pages = [extract_text(doc, i) for i in range(9)]
        records = make_records(n, pages)
        if not records:
            print(f"Unit {n}: no content extracted")
            continue
        ok = upload(records)
        total += ok
        print(f"Unit {n}: {ok}/{len(records)} records uploaded")
    print(f"\nDone. Total: {total} records uploaded.")

if __name__ == "__main__":
    main()