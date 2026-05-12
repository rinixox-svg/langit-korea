#!/usr/bin/env python3
import os
import re
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

try:
    import fitz
    from supabase import create_client
    import requests
except ImportError as e:
    print(f"Error: {e}")
    print("Install: pip install pymupdf supabase-py python-dotenv requests")
    sys.exit(1)

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
STORAGE_BUCKET = "audio-mp3"

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ── Config ──
QUESTION_COUNT = 40
READING_COUNT = 20
LISTENING_START = 21

def parse_pdf(pdf_path):
    """Parse open test PDF, extract questions 1-40."""
    doc = fitz.open(str(pdf_path))
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text

def find_questions(text):
    """Extract questions from parsed PDF text.
    
    EPS-TOPIK open test format:
    - Questions numbered 1-40
    - Each question has 4 options labeled ① ② ③ ④ or (a) (b) (c) (d)
    """
    lines = text.split("\n")
    questions = {}
    current_q = None
    current_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        q_match = re.match(r"^\s*(\d{1,2})\s*[.)]\s*(.+)$", line)
        if q_match:
            num = int(q_match.group(1))
            if 1 <= num <= QUESTION_COUNT:
                if current_q is not None and current_lines:
                    questions[current_q] = "\n".join(current_lines).strip()
                current_q = num
                current_lines = [q_match.group(2).strip()]
                continue

        if current_q is not None:
            current_lines.append(line)

    if current_q is not None and current_lines:
        questions[current_q] = "\n".join(current_lines).strip()

    return questions

def split_question_options(text):
    """Split question text from its options.
    
    Options may be marked as:
    ① ② ③ ④, (a) (b) (c) (d), a. b. c. d., etc.
    """
    if not text:
        return "", ["", "", "", ""]

    option_patterns = [
        re.split(r"[①\s]*[②\s]*[③\s]*[④\s]*", text),
        re.split(r"\([a-d]\)|\b[a-d]\.\)", text, flags=re.IGNORECASE),
        re.split(r"\b[a-d]\.\s", text),
    ]

    parts = None
    for pattern in option_patterns:
        if len(pattern) >= 5:
            parts = pattern
            break

    if parts and len(parts) >= 5:
        question = parts[0].strip()
        options = [p.strip() for p in parts[1:5]]
        return question, options

    return text, ["", "", "", ""]

def extract_answers(text):
    """Extract answer key from the end of PDF (usually on last page).
    
    Format examples:
    [정답] 1. ② 2. ④ 3. ① ...
    or
    <정답> 1-② 2-④ 3-① ...
    """
    answers = {}
    lines = text.split("\n")
    in_answer = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "정답" in line or "ANSWER" in line.upper():
            in_answer = True

        if in_answer:
            ans_matches = re.findall(
                r"(\d{1,2})\s*[-:.]?\s*[①②③④a-dA-D①②③④]",
                line
            )
            for match in ans_matches:
                num = int(match[0])
                ans_char = match[1]
                if 1 <= num <= QUESTION_COUNT:
                    mapping = {"①": "a", "②": "b", "③": "c", "④": "d",
                               "a": "a", "b": "b", "c": "c", "d": "d",
                               "A": "a", "B": "b", "C": "c", "D": "d"}
                    answers[num] = mapping.get(ans_char, "")

            # Also try: "1②", "1-②", "1.②"
            ans_matches2 = re.findall(
                r"(\d{1,2})\s*[-:.)\s]*\s*([①-④a-dA-D])",
                line
            )
            for num_str, ans_str in ans_matches2:
                num = int(num_str)
                if 1 <= num <= QUESTION_COUNT and num not in answers:
                    mapping = {"①": "a", "②": "b", "③": "c", "④": "d",
                               "a": "a", "b": "b", "c": "c", "d": "d",
                               "A": "a", "B": "b", "C": "c", "D": "d"}
                    answers[num] = mapping.get(ans_str, "")

    return answers

def find_mp3_files(mp3_dir, year):
    """Find MP3 files for listening questions (21-40).
    
    Expected naming: open_test_{year}_{question}.mp3
    or                   {year}_{question}.mp3
    """
    mp3_dir = Path(mp3_dir)
    if not mp3_dir.exists():
        return {}

    found = {}
    patterns = [
        f"open_test_{year}_*.mp3",
        f"*_{year}_*.mp3",
        f"*.mp3",
    ]

    for pat in patterns:
        for f in sorted(mp3_dir.glob(pat)):
            q_match = re.search(r"(\d{2})", f.stem)
            if q_match:
                num = int(q_match.group(1))
                if LISTENING_START <= num <= QUESTION_COUNT:
                    found[num] = str(f)
    return found

def upload_mp3(mp3_path, year, question_num):
    """Upload MP3 to Supabase Storage."""
    storage_path = f"open_test/{year}/q{question_num:02d}.mp3"
    try:
        with open(mp3_path, "rb") as f:
            data = f.read()
        supabase.storage.from_(STORAGE_BUCKET).upload(
            storage_path, data, {"content-type": "audio/mpeg"}
        )
    except Exception:
        # File may already exist; try to get public URL anyway
        pass
    
    public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
    return public_url

def build_row(num, question, options, answers, year, mp3_urls, q_type):
    """Build a row dict for soal_eps insertion."""
    q_text, opts = question, options
    answer = answers.get(num, "")
    letters = ["a", "b", "c", "d"]

    return {
        "unit": year,
        "tipe": q_type,
        "teks_soal": q_text[:2000] if q_text else "",
        "pilihan_a": opts[0] if len(opts) > 0 else "",
        "pilihan_b": opts[1] if len(opts) > 1 else "",
        "pilihan_c": opts[2] if len(opts) > 2 else "",
        "pilihan_d": opts[3] if len(opts) > 3 else "",
        "jawaban": answer,
        "audio_url": mp3_urls.get(num, ""),
        "sumber": "open_test",
        "tahun_soal": year,
        "nomor_asli": num,
        "tingkat": "sedang",
        "akses": "free",
    }

def insert_soal(rows):
    """Insert rows into soal_eps table."""
    inserted = 0
    for row in rows:
        try:
            result = supabase.table("soal_eps").insert(row).execute()
            if result.data:
                inserted += 1
                print(f"  OK q{row['nomor_asli']:02d} ({row['tipe']})")
            else:
                print(f"  FAIL q{row['nomor_asli']:02d}: no data returned")
        except Exception as e:
            print(f"  FAIL q{row['nomor_asli']:02d}: {e}")
    return inserted

def main():
    parser = argparse.ArgumentParser(description="Extract EPS-TOPIK open test PDF")
    parser.add_argument("pdf", help="Path to open test PDF file")
    parser.add_argument("--year", type=int, default=2023, help="Test year (default: 2023)")
    parser.add_argument("--mp3-dir", default="open_test_mp3", help="Directory with MP3 audio files")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(1)

    year = args.year
    mp3_dir = args.mp3_dir

    print(f"=== Extracting Open Test {year} ===\n")
    print(f"PDF: {pdf_path}")
    print(f"MP3: {mp3_dir}")
    print()

    # 1. Parse PDF
    print("Parsing PDF...")
    text = parse_pdf(pdf_path)
    print(f"  Pages: {len(fitz.open(str(pdf_path)))}")

    # 2. Find questions
    print("Finding questions...")
    raw_questions = find_questions(text)
    print(f"  Found: {len(raw_questions)} questions")

    if len(raw_questions) < 10:
        print("  Too few questions found. Trying alternative parsing...")
        # Fallback: use raw line-by-line extraction
        lines = text.split("\n")
        q_count = 0
        for line in lines:
            m = re.match(r"\s*(\d{1,2})\s*[.)]", line)
            if m:
                num = int(m.group(1))
                if 1 <= num <= QUESTION_COUNT:
                    if num not in raw_questions:
                        raw_questions[num] = line.strip()
                        q_count += 1
        print(f"  After fallback: {len(raw_questions)} questions")

    # 3. Find answers
    print("Finding answers...")
    answers = extract_answers(text)
    print(f"  Found: {len(answers)} answers")

    # If no answers in PDF, try reading from answers file
    if len(answers) < 10:
        ans_txt = pdf_path.with_suffix(".txt")
        if ans_txt.exists():
            print(f"  Trying answers file: {ans_txt}")
            answers = extract_answers(ans_txt.read_text())
            print(f"  Found: {len(answers)} answers")

    # 4. Find MP3 files
    print("Finding MP3 files...")
    mp3_files = find_mp3_files(mp3_dir, year)
    print(f"  Found: {len(mp3_files)} MP3 files")

    # 5. Upload MP3 files
    print("Uploading MP3 files...")
    mp3_urls = {}
    for q_num, mp3_path in mp3_files.items():
        url = upload_mp3(mp3_path, year, q_num)
        mp3_urls[q_num] = url
        print(f"  q{q_num:02d}: uploaded")

    # 6. Build rows
    print("\nBuilding soal_eps rows...")
    rows = []
    for num in range(1, QUESTION_COUNT + 1):
        q_type = "membaca" if num <= READING_COUNT else "mendengarkan"
        raw = raw_questions.get(num, "")
        q_text, options = split_question_options(raw)
        row = build_row(num, q_text, options, answers, year, mp3_urls, q_type)
        rows.append(row)

    # 7. Report
    print("\n─── Summary ───")
    print(f"Questions parsed: {len([r for r in rows if r['teks_soal']])}/{QUESTION_COUNT}")
    print(f"Reading (1-20): {len([r for r in rows[:20] if r['teks_soal']])}/20")
    print(f"Listening (21-40): {len([r for r in rows[20:] if r['teks_soal']])}/20")
    print(f"Answers found: {len(answers)}/{QUESTION_COUNT}")
    print(f"MP3 files: {len(mp3_files)}/20")

    # 8. Insert
    ans = input("\nInsert into Supabase? (y/N): ")
    if ans.lower() == "y":
        print("\nInserting...")
        ok = insert_soal(rows)
        print(f"\nInserted: {ok}/{len(rows)}")
    else:
        # Save as JSON instead
        out_path = pdf_path.with_suffix(".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"Saved to {out_path}")
        print("Run with --insert to upload to Supabase.")

if __name__ == "__main__":
    main()
