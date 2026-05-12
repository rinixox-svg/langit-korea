#!/usr/bin/env python3
"""
EPS-TOPIK Open Test Full Extractor — Final Integrated Pipeline.

Uses:
- hwp-hwpx-parser for HWP text extraction (best available)
- olefile PrvText for answer keys
- Custom parsers for reading/listening structure
"""
import hashlib
import json
import os
import re
import sys
import zipfile
import glob as _glob
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
STORAGE_BUCKET = "audio-mp3"


# ── HWP Text Extraction (via hwp-hwpx-parser + olefile PrvText) ──

def get_hwp_body(hwp_path: str) -> str:
    """Extract body text from HWP via hwp-hwpx-parser."""
    try:
        from hwp_hwpx_parser import extract_hwp5
        result = extract_hwp5(hwp_path)
        if isinstance(result, tuple) and result[0]:
            return result[0]
        if isinstance(result, str):
            return result
    except:
        pass
    return ""


def get_hwp_prvtext(hwp_path: str) -> str:
    """Extract PrvText (preview text, good for answer keys)."""
    try:
        import olefile, io
        data = Path(hwp_path).read_bytes()
        ole = olefile.OleFileIO(io.BytesIO(data))
        if ole.exists("PrvText"):
            txt = ole.openstream("PrvText").read().decode("utf-16-le", errors="replace")
            ole.close()
            return txt
        ole.close()
    except:
        pass
    return ""


# ── Answer Parsing ──

def parse_answers(text: str) -> dict:
    """Parse answer key from PrvText."""
    answers = {}
    ans_map = {"\u2460": "a", "\u2461": "b", "\u2462": "c", "\u2463": "d",
               "\u2460": "a", "\u2461": "b", "\u2462": "c", "\u2463": "d"}
    # Pattern 1: <1번><④>
    for m in re.finditer(r"<(\d+)\uBC88>\s*<([\u2460-\u2463])>", text):
        n, a = int(m.group(1)), m.group(2)
        if 1 <= n <= 40 and a in ans_map:
            answers[n] = ans_map[a]
    # Pattern 2: <1번><2번>...\n<④><①>...
    nums = [int(m.group(1)) for m in re.finditer(r"<(\d+)\uBC88>", text)]
    opts = [ans_map.get(m.group(1)) for m in re.finditer(r"<([\u2460-\u2463])>", text) if m.group(1) in ans_map]
    for i, n in enumerate(nums):
        if i < len(opts) and opts[i] and 1 <= n <= 40 and n not in answers:
            answers[n] = opts[i]
    # Pattern 3: 21. ① (listening format)
    for m in re.finditer(r"(\d{1,2})\s*[.)]\s*([\u2460-\u2463])", text):
        n = int(m.group(1))
        if 1 <= n <= 40 and n not in answers and m.group(2) in ans_map:
            answers[n] = ans_map[m.group(2)]
    return answers


# ── Listening Parser ──

def parse_listening(text: str) -> list:
    """Parse listening items from PrvText."""
    items = []
    buffer = {}
    ans_map_rev = {"\u2460": "a", "\u2461": "b", "\u2462": "c", "\u2463": "d"}

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\s*(\d{1,2})\s*[.)]?\s*([\u2460-\u2463])?\s*(.*)", line)
        if m:
            num = int(m.group(1))
            if 21 <= num <= 40:
                if buffer and buffer.get("number"):
                    buffer["options"] = buffer.get("options", [])
                    items.append(buffer)
                buffer = {"number": num, "dialog": [], "question": "", "options": [],
                          "answer": ans_map_rev.get(m.group(2), "") if m.group(2) else ""}
                if m.group(3):
                    buffer["question"] = m.group(3).strip()
                continue
        if not buffer:
            continue
        opts = re.findall(r"([\u2460-\u2463])\s*([^\u2460-\u2463]+?)(?=[\u2460-\u2463]|$)", line)
        if opts:
            for lbl, txt in opts:
                buffer.setdefault("options", []).append({"label": lbl, "text": txt.strip()})
            continue
        sm = re.match(r"^[남여Mm]\s*[:.\s]\s*(.*)", line)
        if sm:
            buffer.setdefault("dialog", []).append(sm.group(1).strip())
        elif not buffer.get("question"):
            buffer["question"] = line
        else:
            buffer.setdefault("dialog", []).append(line)

    if buffer and buffer.get("number"):
        buffer["options"] = buffer.get("options", [])
        items.append(buffer)

    return items


# ── MP3 Handling ──

def extract_mp3_from_zip(zip_path: str) -> dict:
    """Extract main question MP3 files from ZIP."""
    mp3 = {}
    try:
        with zipfile.ZipFile(zip_path) as z:
            for name in z.namelist():
                if name.endswith(".mp3"):
                    m = re.search(r"(\d{1,2})", name)
                    if m:
                        qnum = int(m.group(1))
                        if 21 <= qnum <= 40 and not any(x in name for x in ["A-", "B-", "C-", "D-", "_A", "_B", "_C", "_D"]):
                            mp3[qnum] = z.read(name)
    except:
        pass
    return mp3


# ── Build & Insert ──

def build_rows(reading_text: str, listening_items: list, answers: dict, year: int, mp3_urls: dict) -> list:
    """Build soal_eps rows from extracted data."""
    rows = []

    # Reading Q1-20: from text or empty with answer
    for num in range(1, 21):
        q_text = ""
        opts = ["", "", "", ""]
        # Try to extract from reading text
        for line in reading_text.split("\n"):
            line = line.strip()
            if re.match(rf"^\s*{num}\s*[.)]", line) and not line.startswith("|"):
                q_text = line
                break
        row = {
            "unit": year, "tipe": "membaca",
            "teks_soal": q_text[:2000],
            "pilihan_a": "", "pilihan_b": "", "pilihan_c": "", "pilihan_d": "",
            "jawaban": answers.get(num) if answers.get(num) in ("a", "b", "c", "d") else None,
            "sumber": "open_test", "tahun_soal": year, "nomor_asli": num,
            "tingkat": "sedang", "akses": "free",
        }
        # Parse options from reading text if available
        circled = re.findall(r"([\u2460-\u2463])\s*([^\u2460-\u2463]+?)(?=[\u2460-\u2463]|$)", q_text)
        for i, (lbl, txt) in enumerate(circled[:4]):
            row[["pilihan_a", "pilihan_b", "pilihan_c", "pilihan_d"][i]] = txt.strip()[:500]
        rows.append(row)

    # Listening Q21-40
    for num in range(21, 41):
        q_text = ""
        opts = ["", "", "", ""]
        dialog = ""
        audio_url = mp3_urls.get(num, "")

        for item in listening_items:
            if item["number"] == num:
                q_text = item.get("question", "")
                dialog = "\n".join(item.get("dialog", []))
                for i, opt in enumerate(item.get("options", [])[:4]):
                    opts[i] = opt["text"]
                break

        rows.append({
            "unit": year, "tipe": "mendengarkan",
            "teks_soal": q_text[:2000] if q_text else dialog[:2000],
            "audio_teks": dialog[:5000] if dialog else "",
            "pilihan_a": opts[0], "pilihan_b": opts[1],
            "pilihan_c": opts[2], "pilihan_d": opts[3],
            "jawaban": answers.get(num) if answers.get(num) in ("a", "b", "c", "d") else None,
            "audio_url": audio_url,
            "sumber": "open_test", "tahun_soal": year, "nomor_asli": num,
            "tingkat": "sedang", "akses": "free",
        })

    return rows


# ── Main ──

def main():
    import argparse
    parser = argparse.ArgumentParser(description="EPS-TOPIK Open Test Final Extractor")
    parser.add_argument("--hwp", default="downloads/1. *20*.hwp", help="Glob for reading HWP")
    parser.add_argument("--answers", default="downloads/2.*.hwp,downloads/4.*.hwp", help="Answer HWP globs (comma)")
    parser.add_argument("--audio-zip", default="downloads/*.zip", help="Audio ZIP glob")
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-insert", action="store_true")
    args = parser.parse_args()

    import glob as _g
    year = args.year

    # 1. Process reading HWP
    reading_text = ""
    for path in sorted(_g.glob(args.hwp)):
        if not path.endswith(".hwp"):
            continue
        print(f"Reading HWP: {Path(path).name.encode('ascii',errors='replace').decode('ascii')[:50]}")
        reading_text = get_hwp_body(path)
        print(f"  Extracted: {len(reading_text)} chars")
        break

    # 2. Process answer files
    answers = {}
    for pat in args.answers.split(","):
        for path in sorted(_g.glob(pat.strip())):
            if not path.endswith(".hwp"):
                continue
            print(f"Answers HWP: {Path(path).name.encode('ascii',errors='replace').decode('ascii')[:50]}")
            prv = get_hwp_prvtext(path)
            if prv:
                ans = parse_answers(prv)
                answers.update(ans)
                print(f"  Answers: {len(ans)} found (total: {len(answers)})")
            # Also get body for listening
            body = get_hwp_body(path)
            if body and "듣기" in path.replace("\\", "/").split("/")[-1]:
                listening_items = parse_listening(prv or body)
                print(f"  Listening items: {len(listening_items)}")

    # 3. Process listening from answers file
    listening_items = []
    for pat in args.answers.split(","):
        for path in sorted(_g.glob(pat.strip())):
            if "듣기" in path.replace("\\", "/").split("/")[-1]:
                prv = get_hwp_prvtext(path)
                if prv:
                    listening_items = parse_listening(prv)
                    print(f"Listening parsed: {len(listening_items)} items")

    # 4. MP3
    mp3_data = {}
    for path in sorted(_g.glob(args.audio_zip)):
        if not path.endswith(".zip"):
            continue
        print(f"Audio ZIP: {Path(path).name.encode('ascii',errors='replace').decode('ascii')[:60]}")
        mp3_data = extract_mp3_from_zip(path)
        print(f"  MP3 files: {len(mp3_data)}")

    # 5. Upload MP3 + get URLs
    supabase = None
    if not args.no_insert and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    mp3_urls = {}
    for qnum, data in mp3_data.items():
        if supabase:
            path = f"open_test/{year}/q{qnum:02d}.mp3"
            try:
                supabase.storage.from_(STORAGE_BUCKET).upload(path, data, {"content-type": "audio/mpeg"})
            except:
                pass
            try:
                mp3_urls[qnum] = supabase.storage.from_(STORAGE_BUCKET).get_public_url(path)
            except:
                mp3_urls[qnum] = ""

    # 6. Build rows
    rows = build_rows(reading_text, listening_items, answers, year, mp3_urls)

    print(f"\n=== Summary ===")
    r_txt = len([r for r in rows[:20] if r["teks_soal"] and len(r["teks_soal"]) > 5])
    l_txt = len([r for r in rows[20:] if r["teks_soal"] and len(r["teks_soal"]) > 5])
    a_count = len(answers)
    m_count = len(mp3_urls)
    print(f"Reading: {r_txt}/20 with text, {a_count}/40 answers")
    print(f"Listening: {l_txt}/20 with text, {m_count}/20 audio")

    if args.no_insert:
        out = f"open_test_{year}_full.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"Saved to {out}")
        return

    auto = args.yes
    try:
        ans = input(f"\nInsert {len(rows)} questions? (y/N): ") if not auto else "y"
    except:
        ans = "n"

    if ans.lower() == "y":
        ok = 0
        for row in rows:
            try:
                exist = supabase.table("soal_eps").select("id").eq("sumber", "open_test").eq("tahun_soal", year).eq("nomor_asli", row["nomor_asli"]).execute()
                if exist.data and len(exist.data) > 0:
                    print(f"  SKIP q{row['nomor_asli']:02d}")
                    continue
                supabase.table("soal_eps").insert(row).execute()
                ok += 1
                print(f"  OK q{row['nomor_asli']:02d} ({row['tipe']})")
            except Exception as e:
                err = str(e).encode("ascii", errors="replace").decode("ascii")
                print(f"  FAIL q{row['nomor_asli']:02d}: {err[:100]}")
        print(f"Inserted: {ok}/{len(rows)}")
    else:
        out = f"open_test_{year}_full.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"Saved to {out}")


if __name__ == "__main__":
    main()
