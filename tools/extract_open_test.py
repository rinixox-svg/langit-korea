#!/usr/bin/env python3
import os, re, io, sys, json, zipfile, argparse
from pathlib import Path
from dotenv import load_dotenv

try:
    import requests, olefile
    from supabase import create_client
except ImportError as e:
    print("Error:", e)
    sys.exit(1)

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
STORAGE_BUCKET = "audio-mp3"
BASE_URL = "https://epstopik.hrdkorea.or.kr"

# ── Download ──

def download_files():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    s.get(BASE_URL + "/epstopik/book/pub/publicWorkBookList.do?lang=en", timeout=30)
    main = s.get(BASE_URL + "/epstopik/book/pub/publicWorkBookList.do?lang=en", timeout=30)
    links = re.findall(r'href="([^"]*\.(?:hwp|zip))"', main.text)
    files = []
    for l in links:
        url = BASE_URL + l
        try:
            r = s.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > 5000:
                name = l.split("/")[-1]
                files.append({"name": name, "data": r.content, "url": url, "size": len(r.content)})
                fname = name.encode("ascii", errors="replace").decode("ascii")
                print("  {} bytes: {}".format(len(r.content), fname[:60]))
        except Exception as e:
            pass
    return files

# ── HWP Text ──

def hwp_text(data):
    try:
        ole = olefile.OleFileIO(io.BytesIO(data))
        if ole.exists("PrvText"):
            txt = ole.openstream("PrvText").read().decode("utf-16-le", errors="replace")
            ole.close()
            return txt
        ole.close()
    except:
        pass
    return ""

# ── Parse Answers ──

def parse_answers_file(text):
    """Parse answers from PrvText of answer HWP.
    Format: <1번><4> or <1번><①> or just: 1. ②  2. ④ ...
    """
    answers = {}
    # Pattern 1: <1번><④> or <1><④>
    for m in re.finditer(r"<(\d+)[번]?>?\s*><[①-④a-dA-D①②③④]", text):
        num = int(m.group(1))
        num = num if num <= 40 else (num - 1)  # handle off-by-one
        # Extract answer from context
        ctx = text[m.start():m.start()+20]
        for c in "①②③④":
            if c in ctx:
                answers[num] = {"①":"a","②":"b","③":"c","④":"d"}[c]
                break
    # Pattern 2: 1. ② or 1② etc
    if len(answers) < 5:
        for m in re.finditer(r"(\d{1,2})\s*[.)\s]*\s*([①-④])", text):
            num = int(m.group(1))
            if 1 <= num <= 40:
                answers[num] = {"①":"a","②":"b","③":"c","④":"d"}[m.group(2)]
    return answers

# ── Parse Questions ──

def parse_listening_questions(text):
    """Parse listening questions from answer+script HWP.
    Format:
    21. ①
    Some text or dialog
    22. ②
    ...
    """
    questions = {}
    lines = text.split("\n")
    current_q = None
    current_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(\d{1,2})\s*[.)]\s*$", line)
        if m:
            num = int(m.group(1))
            if 21 <= num <= 40:
                if current_q and current_lines:
                    questions[current_q] = "\n".join(current_lines)
                current_q = num
                current_lines = []
                continue
            elif 21 > num >= 1:
                # Check if next line has answer pattern
                pass
        # Check for answer on same line: "21. ①"
        m2 = re.match(r"^(\d{1,2})\s*[.)]\s*([①-④])\s*(.*)$", line)
        if m2:
            num = int(m2.group(1))
            if 21 <= num <= 40:
                if current_q and current_lines:
                    questions[current_q] = "\n".join(current_lines)
                current_q = num
                current_lines = [m2.group(3).strip()] if m2.group(3).strip() else []
                continue
        if current_q is not None:
            current_lines.append(line)
    if current_q and current_lines:
        questions[current_q] = "\n".join(current_lines)
    return questions


def build_question(num, text, answers, qtype):
    """Build question data for a number."""
    ans = answers.get(num, "")
    opts = ["", "", "", ""]
    q_text = text or ""

    # Try to split options from text if they look like dialog options
    opt_lines = [l for l in q_text.split("\n") if l.strip()]
    if qtype == "mendengarkan" and len(opt_lines) >= 3:
        # Use first line as question, rest as context
        q_text = opt_lines[0]
        opts = opt_lines[-4:] if len(opt_lines) >= 6 else ["", "", "", ""]
        # Pad options
        opts = opts + [""] * (4 - len(opts))

    return {
        "unit": 2023, "tipe": qtype,
        "teks_soal": q_text[:2000] if q_text else "",
        "pilihan_a": opts[0] if len(opts) > 0 else "",
        "pilihan_b": opts[1] if len(opts) > 1 else "",
        "pilihan_c": opts[2] if len(opts) > 2 else "",
        "pilihan_d": opts[3] if len(opts) > 3 else "",
        "jawaban": ans,
        "audio_url": "",
        "sumber": "open_test", "tahun_soal": 2023, "nomor_asli": num,
        "tingkat": "sedang", "akses": "free",
    }

# ── Main ──

def main():
    parser = argparse.ArgumentParser(description="EPS-TOPIK Open Test Extractor")
    parser.add_argument("--download", action="store_true", help="Download from eps.go.kr")
    parser.add_argument("--no-insert", action="store_true", help="Save JSON only")
    parser.add_argument("--yes", action="store_true", help="Auto-confirm insert")
    parser.add_argument("--year", type=int, default=2023)
    args = parser.parse_args()

    if not args.download:
        print("Use --download to fetch from eps.go.kr")
        print("Or provide: --pdf FILE [--answers FILE] [--audio-zip FILE]")
        return

    print("Downloading open test files...")
    files = download_files()
    if not files:
        print("No files downloaded.")
        return

    # Extract content from each file type
    # File order: 0=reading1, 1=reading2, 2=reading_ans1, 3=reading_ans2,
    #             4=listening1, 5=listening2, 6=listening_ans1, 7=listening_ans2,
    #             8=audio1, 9=audio2
    reading_text = ""
    listening_text = ""
    answer_text = ""
    listening_script_text = ""

    for i, f in enumerate(files):
        txt = hwp_text(f["data"])
        if not txt:
            continue

        if i == 0:
            reading_text = txt
        elif i == 4:
            listening_text = txt
        elif i == 6:
            listening_script_text = txt
            answer_text += txt + "\n"
        elif i in (2, 3, 7):
            answer_text += txt + "\n"

    print("")
    print("Reading text: {} chars".format(len(reading_text)))
    print("Listening text: {} chars".format(len(listening_text)))
    print("Answers text: {} chars".format(len(answer_text)))
    print("Listening scripts: {} chars".format(len(listening_script_text)))

    # Parse answers
    print("\nParsing answers...")
    answers = parse_answers_file(answer_text)
    print("  Found: {} answers".format(len(answers)))
    for n in sorted(answers)[:10]:
        sys.stdout.buffer.write("    Q{} -> {}\n".format(n, answers[n]).encode())

    # Parse listening questions from script
    print("\nParsing listening questions...")
    listen_qs = {}
    if listening_script_text:
        listen_qs = parse_listening_questions(listening_script_text)
        print("  Parsed: {} questions".format(len(listen_qs)))
    else:
        print("  No script text available")

    # MP3 from ZIP
    mp3_data = {}
    for f in files:
        if f["name"].endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(f["data"])) as z:
                    for name in z.namelist():
                        if name.endswith(".mp3"):
                            m = re.search(r"(\d{2})", name)
                            num = int(m.group(1)) if m else 0
                            if 21 <= num <= 40:
                                mp3_data[num] = z.read(name)
            except:
                pass

    print("\nMP3 files: {}".format(len(mp3_data)))

    # Upload MP3 & build rows
    supabase = None
    if not args.no_insert and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    mp3_urls = {}
    for num, data in mp3_data.items():
        if supabase:
            path = "open_test/{}/q{:02d}.mp3".format(args.year, num)
            try:
                supabase.storage.from_(STORAGE_BUCKET).upload(path, data, {"content-type": "audio/mpeg"})
            except:
                pass
            try:
                mp3_urls[num] = supabase.storage.from_(STORAGE_BUCKET).get_public_url(path)
            except:
                mp3_urls[num] = ""

    rows = []
    for num in range(1, 41):
        qtype = "membaca" if num <= 20 else "mendengarkan"
        q_text = ""
        if num <= 20:
            # Reading: extract from reading text if available
            if reading_text:
                for line in reading_text.split("\n"):
                    if line.strip().startswith(str(num)):
                        q_text = line.strip()
        else:
            q_text = listen_qs.get(num, "")

        row = build_question(num, q_text, answers, qtype)
        if num in mp3_urls:
            row["audio_url"] = mp3_urls[num]
        rows.append(row)

    # Summary
    r_ok = len([r for r in rows[:20] if r["teks_soal"]])
    l_ok = len([r for r in rows[20:] if r["teks_soal"]])
    a_ok = len(answers)
    m_ok = len(mp3_data)

    print("\n\u2500\u2500\u2500 Summary \u2500\u2500\u2500".encode("ascii", errors="replace").decode("ascii"))
    print("Reading (1-20): {}/20".format(r_ok))
    print("Listening (21-40): {}/20".format(l_ok))
    print("Answers: {}/40".format(a_ok))
    print("MP3: {}/20".format(m_ok))

    if args.no_insert:
        out = "open_test_{}.json".format(args.year)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print("\nSaved to", out)
        return

    auto_yes = "--yes" in sys.argv or os.environ.get("EXTRACT_AUTO_YES") == "1"
    if auto_yes:
        ans = "y"
    else:
        try:
            ans = input("\nInsert {} questions into Supabase? (y/N): ".format(len(rows)))
        except (EOFError, KeyboardInterrupt):
            ans = "n"

    if ans.lower() == "y":
        ok = 0
        for row in rows:
            try:
                supabase.table("soal_eps").insert(row).execute()
                ok += 1
                print("  OK q{:02d} ({})".format(row["nomor_asli"], row["tipe"]))
            except Exception as e:
                print("  FAIL q{:02d}: {}".format(row["nomor_asli"], e))
        print("Inserted: {}/{}".format(ok, len(rows)))
    else:
        out = "open_test_{}.json".format(args.year)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print("Saved to", out)


def try_convert_hwp_to_pdf(hwp_path, out_dir):
    """Try to convert HWP to PDF using available converters."""
    import subprocess
    # Check soffice.com (LibreOffice console)
    lo_paths = [
        "soffice.com", "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.com",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.com",
    ]
    for lo in lo_paths:
        try:
            subprocess.run([lo, "--version"], capture_output=True, timeout=10)
            result = subprocess.run(
                [lo, "--headless", "--convert-to", "pdf", "--outdir", out_dir, hwp_path],
                capture_output=True, timeout=120
            )
            if result.returncode == 0:
                pdf_path = Path(out_dir) / (Path(hwp_path).stem + ".pdf")
                if pdf_path.exists() and pdf_path.stat().st_size > 1000:
                    return str(pdf_path)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None

def convert_hwp_command(args):
    """--convert-hwp subcommand: download HWP files and try to convert to PDF."""
    if not args.download:
        print("Downloading first (--download is implied with --convert-hwp)...")
        args.download = True
    return "proceed"

if __name__ == "__main__":
    # Add --convert-hwp arg
    import sys as _sys
    if "--convert-hwp" in _sys.argv:
        # Run download + conversion
        import subprocess, tempfile
        _sys.argv.remove("--convert-hwp")
        print("Step 1: Downloading HWP files from eps.go.kr...")
        # Quick download
        _s = requests.Session()
        _s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        _s.get(BASE_URL + "/epstopik/book/pub/publicWorkBookList.do?lang=en", timeout=30)
        _m = _s.get(BASE_URL + "/epstopik/book/pub/publicWorkBookList.do?lang=en", timeout=30)
        _links = re.findall(r'href="([^"]*\.(?:hwp|zip))"', _m.text)
        os.makedirs("downloads", exist_ok=True)
        for _l in _links:
            _url = BASE_URL + _l
            _name = _l.split("/")[-1]
            try:
                _r = _s.get(_url, timeout=60)
                if _r.status_code == 200 and len(_r.content) > 5000:
                    with open(os.path.join("downloads", _name), "wb") as _f:
                        _f.write(_r.content)
                    _safe = _name.encode("ascii", errors="replace").decode("ascii")
                    print("  OK: {} ({} bytes)".format(_safe[:60], len(_r.content)))
            except Exception:
                pass
        print("\nStep 2: Converting HWP to PDF...")
        _converted = 0
        _out = Path("downloads")
        for _f in sorted(_out.glob("*.hwp")):
            _pdf = try_convert_hwp_to_pdf(str(_f), str(_out))
            _safe = _f.name.encode("ascii", errors="replace").decode("ascii")
            if _pdf:
                print("  OK: {} -> {}".format(_safe[:50], Path(_pdf).name))
                _converted += 1
            else:
                print("  FAIL: {} (no converter)".format(_safe[:50]))
        if _converted == 0:
            print("\n" + "="*60)
            print("TIDAK BISA KONVERSI HWP KE PDF OTOMATIS.")
            print("Solusi: online converter https://www.zamzar.com/convert/hwp-to-pdf/")
            print("Atau install Hancom Viewer: https://www.hancom.com/cs_center/csDownload.do")
            print("="*60)
        else:
            print("\n{} PDF files created in downloads/".format(_converted))
            print("Sekarang jalankan: python tools/extract_open_test.py --pdf downloads/*.pdf")
        _sys.exit(0)
    main()
