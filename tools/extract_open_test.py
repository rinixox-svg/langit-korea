#!/usr/bin/env python3
import os, re, io, sys, json, zipfile, argparse, zlib
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
    """Extract body text via hwp-hwpx-parser."""
    try:
        from hwp_hwpx_parser import extract_hwp5
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".hwp", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        result = extract_hwp5(tmp_path)
        os.unlink(tmp_path)
        if isinstance(result, tuple) and result[0]:
            return result[0]
        if isinstance(result, str) and result:
            return result
    except:
        pass
    return ""

def hwp_prvtext(data):
    """Extract preview text via olefile PrvText, fallback to BodyText zlib."""
    try:
        ole = olefile.OleFileIO(io.BytesIO(data))
        txt = ""
        if ole.exists("PrvText"):
            txt = ole.openstream("PrvText").read().decode("utf-16-le", errors="replace")
        # Also try BodyText for answers that might be missing from PrvText
        if ole.exists("BodyText/Section0"):
            raw = ole.openstream("BodyText/Section0").read()
            try:
                d = zlib.decompress(raw, -zlib.MAX_WBITS)
                body = d.decode("utf-16-le", errors="replace")
                # Extract lines with answer patterns (number + circled option)
                body_answers = []
                for line in body.split("\n"):
                    line = line.strip()
                    if re.search(r"\d{1,2}\s*[.)]\s*[\u2460-\u2463]", line):
                        body_answers.append(line)
                if body_answers:
                    txt += "\n" + "\n".join(body_answers)
            except:
                pass
        ole.close()
        return txt
    except:
        return ""

# ── Parse Answers ──

def parse_answers_file(text):
    """Parse answers from PrvText of answer HWP.
    Formats:
    - <1번><④> (reading answers)
    - 21. ① (listening answers) 
    - 1. ②  2. ④ 
    """
    answers = {}
    ans_map = {"\u2460":"a","\u2461":"b","\u2462":"c","\u2463":"d",
               "①":"a","②":"b","③":"c","④":"d",
               "a":"a","b":"b","c":"c","d":"d",
               "A":"a","B":"b","C":"c","D":"d"}

    # Pattern 1: <1번><④>
    for m in re.finditer(r"<(\d+)\uBC88>\s*<([\u2460-\u2463])>", text):
        num = int(m.group(1))
        if 1 <= num <= 40 and m.group(2) in ans_map:
            answers[num] = ans_map[m.group(2)]

    # Pattern 2: consecutive <1번><2번>... then <④><①>...
    nums = [int(m.group(1)) for m in re.finditer(r"<(\d+)\uBC88>", text)]
    opts = [ans_map.get(m.group(1)) for m in re.finditer(r"<([\u2460-\u2463abcdABCD])>", text)
            if m.group(1) in ans_map]
    for i, num in enumerate(nums):
        if i < len(opts) and opts[i] and 1 <= num <= 40 and num not in answers:
            answers[num] = opts[i]

    # Pattern 3: 21. ① (listening answers format)
    for m in re.finditer(r"(\d{1,2})\s*[.)]\s*([\u2460-\u2463])", text):
        num = int(m.group(1))
        if 1 <= num <= 40 and m.group(2) in ans_map and num not in answers:
            answers[num] = ans_map[m.group(2)]

    # Pattern 4: 1. ② or 1② etc
    for m in re.finditer(r"(\d{1,2})\s*[.)\s]*\s*([①-④a-d])", text, re.IGNORECASE):
        num = int(m.group(1))
        ans = m.group(2)
        if 1 <= num <= 40 and num not in answers:
            answers[num] = ans_map.get(ans, "")

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


def build_row(num, q_text, opts, answers, year, mp3_urls, qtype):
    """Build soal_eps row."""
    ans = answers.get(num)
    return {
        "unit": year, "tipe": qtype,
        "teks_soal": q_text[:2000] if q_text else "",
        "pilihan_a": opts[0] if len(opts) > 0 else "",
        "pilihan_b": opts[1] if len(opts) > 1 else "",
        "pilihan_c": opts[2] if len(opts) > 2 else "",
        "pilihan_d": opts[3] if len(opts) > 3 else "",
        "jawaban": ans if ans in ("a","b","c","d") else None,
        "audio_url": mp3_urls.get(num, ""),
        "sumber": "open_test", "tahun_soal": year, "nomor_asli": num,
        "tingkat": "sedang", "akses": "free",
    }

# ── Listening PDF Processor ──

def _process_listening_pdf(args, listening_items, _glob, split_listening_items_fn):
    """Process listening PDF and merge items into listening_items list."""
    import fitz
    for lpath in _glob.glob(args.listening_pdf):
        safe = lpath.encode("ascii", errors="replace").decode("ascii")
        print("Listening PDF:", safe[:80])
        try:
            ldoc = fitz.open(lpath)
            lblocks = []
            for pn in range(len(ldoc)):
                pd = ldoc[pn].get_text("dict")
                for b in pd.get("blocks", []):
                    if b["type"] == 0:
                        for line in b.get("lines", []):
                            t = "".join(s["text"] for s in line.get("spans", []))
                            if t.strip():
                                bb = line["bbox"]
                                lblocks.append({"text": t.strip(), "page": pn+1,
                                                "x0": round(bb[0],1), "y0": round(bb[1],1)})
            ldoc.close()
            print(f"  {len(lblocks)} blocks")
            litems = split_listening_items_fn(lblocks)
            if litems:
                existing = {li["number"]: li for li in listening_items}
                for li in litems:
                    existing[li["number"]] = li
                listening_items.clear()
                listening_items.extend(list(existing.values()))
                listening_items.sort(key=lambda x: x["number"])
                print(f"  Listening items: {len(listening_items)}")
        except ImportError as e:
            print(f"  PDF mode requires PyMuPDF + parsing_rules: {e}")
        except Exception as e:
            err = str(e).encode("ascii", errors="replace").decode("ascii")
            print(f"  Listening PDF error: {err[:80]}")

# ── Image Extraction ──

def _extract_and_save_images(pdf_pattern, year, supabase):
    """Extract images from reading PDF, match to questions, upload to Storage."""
    import glob as _g, hashlib, os
    import fitz
    bucket = STORAGE_BUCKET
    for path in _g.glob(pdf_pattern):
        safe = path.encode("ascii", errors="replace").decode("ascii")
        print("Images:", safe[:60])
        doc = fitz.open(path)
        
        # Get text blocks with positions
        all_blocks = []
        for i in range(len(doc)):
            pd = doc[i].get_text("dict")
            for b in pd.get("blocks", []):
                if b["type"] == 0:
                    for line in b.get("lines", []):
                        t = "".join(s["text"] for s in line.get("spans", []))
                        if t.strip():
                            bb = line["bbox"]
                            all_blocks.append({"text": t.strip(), "page": i+1, "y0": bb[1]})
        
        # Build question y-ranges
        q_ranges = []
        cur = None
        for blk in all_blocks:
            m = re.match(r"\s*(\d{1,2})\s*[\.\s\)]", blk["text"])
            if m:
                n = int(m.group(1))
                if 1 <= n <= 20:
                    if cur:
                        cur["y1"] = blk["y0"]
                    cur = {"number": n, "y0": blk["y0"], "y1": float('inf'), "page": blk["page"]}
                    q_ranges.append(cur)
            if cur and cur["y1"] == float('inf'):
                cur["y1"] = blk.get("y1", blk["y0"] + 20) if "y1" in blk else blk["y0"] + 20
        
        # Extract and match images
        matched = 0
        for i in range(len(doc)):
            page = doc[i]
            for img in page.get_images(full=True):
                xref = img[0]
                base = doc.extract_image(xref)
                if base and base["width"] > 30 and base["height"] > 30:
                    # Find image y-position
                    img_y0, img_page = i * 200, i+1  # fallback: estimate by page
                    try:
                        for ib in page.get_image_bbox():
                            if ib[0] == xref:
                                img_y0 = ib[2]
                                break
                    except:
                        pass
                    
                    matched_q = 0
                    for qr in q_ranges:
                        if img_page == qr["page"] and qr["y0"] - 50 <= img_y0 <= qr["y1"] + 200:
                            matched_q = qr["number"]
                            break
                    
                    sha = hashlib.sha256(base["image"]).hexdigest()[:16]
                    ext = base["ext"]
                    fname = "open_test_{}_q{}_img_{}.{}".format(year, matched_q, sha, ext)
                    spath = "open_test/{}/images/{}".format(year, fname)
                    
                    try:
                        supabase.storage.from_(bucket).upload(spath, base["image"], {"content-type": "image/{}".format(ext)})
                    except:
                        pass
                    url = supabase.storage.from_(bucket).get_public_url(spath)
                    
                    if matched_q:
                        supabase.table("soal_eps").update({"gambar_url": url}).eq("sumber", "open_test").eq("tahun_soal", year).eq("nomor_asli", matched_q).execute()
                        matched += 1
                        print("  Q{} <- image".format(matched_q))
        
        doc.close()
        print("  {} images matched to questions".format(matched))

# ── Main ──

def main():
    parser = argparse.ArgumentParser(description="EPS-TOPIK Open Test Extractor")
    parser.add_argument("--download", action="store_true", help="Download from eps.go.kr")
    parser.add_argument("--no-insert", action="store_true", help="Save JSON only")
    parser.add_argument("--yes", action="store_true", help="Auto-confirm insert")
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--pdf", help="Path to reading PDF file (or glob pattern)")
    parser.add_argument("--listening-pdf", help="Path to listening PDF file")
    parser.add_argument("--hwp", help="Path to reading HWP file (or glob pattern)")
    parser.add_argument("--answers", help="Path to answer file(s) (PDF/HWP, comma-separated)")
    parser.add_argument("--audio-zip", help="Path to audio ZIP file")
    args = parser.parse_args()
    year = args.year

    if not args.download and not args.pdf and not args.hwp:
        print("Use --download to fetch from eps.go.kr")
        print("Or provide: --hwp FILE [--answers FILE] [--audio-zip FILE]")
        return

    reading_text = ""
    listening_text = ""
    answer_text = ""
    listening_script_text = ""
    mp3_data = {}
    import collections
    answer_sources = collections.OrderedDict()

    # ── Local file mode ──
    if args.hwp or args.pdf or args.audio_zip:
        import glob as _glob
        reading_text = ""
        reading_items = []  # For parsed questions from PDF
        listening_items = []
        if args.pdf:
            try:
                import fitz
                import sys as _sys_for_path
                # Add both project root and forensic package to path
                _script_dir = os.path.dirname(os.path.abspath(__file__))
                _project_root = os.path.abspath(os.path.join(_script_dir, ".."))
                _forensic_dir = os.path.join(_project_root, "epstopik_forensic_scraper")
                for _p in [_forensic_dir, _project_root]:
                    if _p not in _sys_for_path.path:
                        _sys_for_path.path.insert(0, _p)
                # Import directly from file path to avoid package init chain
                import importlib.util as _imp_util
                _spec = _imp_util.spec_from_file_location(
                    "parsing_rules",
                    os.path.join(_forensic_dir, "scraper", "parsing_rules.py")
                )
                _parsing_rules = _imp_util.module_from_spec(_spec)
                _spec.loader.exec_module(_parsing_rules)
                split_reading_questions = _parsing_rules.split_reading_questions
                split_listening_items = _parsing_rules.split_listening_items
                extract_options = _parsing_rules.extract_options
                is_question_start = _parsing_rules.is_question_start
                clean_block_text = _parsing_rules.clean_block_text
                for path in _glob.glob(args.pdf):
                    safe = path.encode("ascii", errors="replace").decode("ascii")
                    print("PDF:", safe[:80])
                    doc = fitz.open(path)
                    blocks = []
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        page_dict = page.get_text("dict")
                        for block in page_dict.get("blocks", []):
                            if block["type"] == 0:
                                for line in block.get("lines", []):
                                    text = "".join(s["text"] for s in line.get("spans", []))
                                    if text.strip():
                                        bbox = line["bbox"]
                                        blocks.append({
                                            "text": text.strip(),
                                            "x0": round(bbox[0], 1),
                                            "y0": round(bbox[1], 1),
                                            "x1": round(bbox[2], 1),
                                            "y1": round(bbox[3], 1),
                                            "page": page_num + 1,
                                        })
                    doc.close()
                    print(f"  Extracted {len(blocks)} text blocks")
                    # Try reading mode
                    passage, qgroups = split_reading_questions(blocks)
                    if qgroups:
                        print(f"  Reading: {len(qgroups)} question groups")
                        for qg in qgroups:
                            qtext_parts = []
                            opts = []
                            qnum = None
                            for b in qg:
                                t = b.get("text", "")
                                is_q, n = is_question_start(t)
                                if is_q and n:
                                    qnum = n
                                    m = re.match(r"^\s*\d{1,2}\s*[\.\s\)]\s*(.*)", t, re.DOTALL)
                                    if m and m.group(1).strip():
                                        qtext_parts.append(m.group(1).strip())
                                else:
                                    ex = extract_options(t)
                                    if ex:
                                        opts.extend(ex)
                                    elif t.strip():
                                        qtext_parts.append(t.strip())
                            if qnum:
                                reading_items.append({
                                    "number": qnum,
                                    "text": " ".join(qtext_parts),
                                    "options": opts,
                                })
                        reading_text = passage or ""
            except Exception as e:
                err = str(e).encode("ascii", errors="replace").decode("ascii")
                print(f"  PDF processing error: {err[:100]}")
    
    if args.listening_pdf:
        _process_listening_pdf(args, listening_items, _glob, split_listening_items)
        if args.hwp:
            for path in _glob.glob(args.hwp):
                safe = path.encode("ascii", errors="replace").decode("ascii")
                print("Reading:", safe[:80])
                data = Path(path).read_bytes()
                txt = hwp_text(data)
                if len(txt) > len(reading_text):
                    reading_text = txt
                if not answer_text:
                    prv = hwp_prvtext(data)
                    if len(prv) > len(answer_text):
                        answer_text = prv
        if args.answers:
            for single_pat in args.answers.split(","):
                for path in _glob.glob(single_pat.strip()):
                    safe = path.encode("ascii", errors="replace").decode("ascii")
                    print("Answers:", safe[:80])
                    if path.endswith(".pdf"):
                        try:
                            doc = fitz.open(path)
                            txt = ""
                            for page in doc:
                                txt += page.get_text()
                            doc.close()
                            if txt:
                                answer_text += txt + "\n"
                        except:
                            pass
                    else:
                        data = Path(path).read_bytes()
                        prv = hwp_prvtext(data)
                        if prv:
                            answer_text += prv + "\n"
                        else:
                            txt = hwp_text(data)
                            if txt:
                                answer_text += txt + "\n"
        if args.audio_zip:
            for path in _glob.glob(args.audio_zip):
                safe = path.encode("ascii", errors="replace").decode("ascii")
                print("Audio:", safe[:80])
                try:
                    with zipfile.ZipFile(path) as z:
                        for name in z.namelist():
                            if name.endswith(".mp3"):
                                m = re.search(r"(\d{2})", name)
                                num = int(m.group(1)) if m else 0
                                if 21 <= num <= 40:
                                    mp3_data[num] = z.read(name)
                except Exception as e:
                    err = str(e).encode("ascii", errors="replace").decode("ascii")
                    print("  ZIP error:", err[:80])
        if not reading_text and not answer_text and not mp3_data:
            print("No data extracted. Check file paths.")
            return

    # ── Download mode ──
    else:
        print("Downloading open test files...")
        files = download_files()
        if not files:
            print("No files downloaded.")
            return

        # File order: 0=reading1, 1=reading2, 2=reading_ans1, 3=reading_ans2,
        #             4=listening1, 5=listening2, 6=listening_ans1, 7=listening_ans2,
        #             8=audio1, 9=audio2
        for i, f in enumerate(files):
            txt = hwp_text(f["data"])
            if i == 0 and txt:
                reading_text = txt
            elif i == 4 and txt:
                listening_text = txt
            elif i == 6 and txt:
                listening_script_text = txt
            
            prv = hwp_prvtext(f["data"])
            if i in (2, 3, 6, 7) and prv:
                answer_sources[i] = prv

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

    # Parse answers: read from each file, only keep first answer per question
    answers = {}
    if answer_sources:
        for src_idx in sorted(answer_sources.keys(), reverse=True):
            src_answers = parse_answers_file(answer_sources[src_idx])
            for num, ans in src_answers.items():
                if num not in answers:
                    answers[num] = ans
        answer_text = "\n".join(answer_sources.values())
    elif answer_text:
        answers = parse_answers_file(answer_text)

    print("")
    print("Reading text: {} chars".format(len(reading_text)))
    print("Listening text: {} chars".format(len(listening_text)))
    print("Answers text: {} chars".format(len(answer_text)))
    print("Listening scripts: {} chars".format(len(listening_script_text)))

    print("\nAnswers: {} found".format(len(answers)))
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
        opts = ["", "", "", ""]

        if num <= 20:
            found = False
            for ri in reading_items:
                if ri["number"] == num:
                    q_text = ri.get("text", "")
                    ropts = ri.get("options", [])
                    if ropts:
                        for i, opt in enumerate(ropts[:4]):
                            if isinstance(opt, dict):
                                opts[i] = opt.get("text", "")[:500]
                            else:
                                opts[i] = str(opt)[:500]
                    found = True
                    break
            if not found and reading_text:
                for line in reading_text.split("\n"):
                    if line.strip().startswith(str(num)):
                        q_text = line.strip()
                        break
        else:
            # Listening: prefer parsed listening items (from PDF parsing_rules)
            found = False
            for li in listening_items:
                if li["number"] == num:
                    q_text = li.get("question", "")
                    if not q_text:
                        q_text = li.get("dialog_script", "")[:100]
                    lopts = li.get("options", [])
                    if lopts:
                        script = li.get("dialog_script", "")
                        q_text = li.get("question", "") or script[:2000]
                        for i, opt in enumerate(lopts[:4]):
                            if isinstance(opt, dict):
                                opts[i] = opt["text"][:500]
                            else:
                                opts[i] = str(opt)[:500]
                    found = True
                    break
            if not found:
                q_text = listen_qs.get(num, "")

        row = build_row(num, q_text, opts, answers, year, mp3_urls, qtype)
        if num in mp3_urls:
            row["audio_url"] = mp3_urls[num]
        rows.append(row)

    # Summary
    r_ok = len([r for r in rows[:20] if r["teks_soal"]])
    l_ok = len([r for r in rows[20:] if r["teks_soal"]])
    a_ok = len(answers)
    m_ok = len(mp3_data)

    print("\n===================================".encode("ascii", errors="replace").decode("ascii"))
    print("Reading (1-20): {}/20  (from PDF blocks: {})".format(r_ok, len(reading_items)))
    print("Listening (21-40): {}/20  (from PDF blocks: {})".format(l_ok, len(listening_items)))
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

    if args.pdf and not args.no_insert:
        _extract_and_save_images(args.pdf, year, supabase)
    
    if ans.lower() == "y":
        ok = 0
        skip = 0
        for row in rows:
            try:
                exist = supabase.table("soal_eps").select("id").eq("sumber", "open_test").eq("tahun_soal", year).eq("nomor_asli", row["nomor_asli"]).execute()
                if exist.data and len(exist.data) > 0:
                    supabase.table("soal_eps").update(row).eq("sumber", "open_test").eq("tahun_soal", year).eq("nomor_asli", row["nomor_asli"]).execute()
                    ok += 1
                    print("  UPD q{:02d} ({})".format(row["nomor_asli"], row["tipe"]))
                    continue
                supabase.table("soal_eps").insert(row).execute()
                ok += 1
                print("  OK q{:02d} ({})".format(row["nomor_asli"], row["tipe"]))
            except Exception as e:
                err = str(e).encode("ascii", errors="replace").decode("ascii")
                print("  FAIL q{:02d}: {}".format(row["nomor_asli"], err[:150]))
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
