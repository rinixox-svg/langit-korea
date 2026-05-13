"""Clean extraction of questions + options from PDFs. No page separators, no metadata noise."""
import sys, glob, re, os
sys.path.insert(0, "epstopik_forensic_scraper")
from scraper.parsing_rules import extract_options
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

supa = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
YEAR = 2023
import fitz

def clean_line(l):
    """Remove metadata noise from a line."""
    l = l.strip()
    if not l:
        return ""
    # Skip pure metadata lines
    if re.match(r"^\d{4}\s*-\s*\d+\s*-\s*\d+", l):  # "2025 - 253 - 2"
        return ""
    if "EPS-TOPIK" in l or "Adobe" in l or "Photoshop" in l:
        return ""
    if re.match(r"^\d+x\d+", l):  # pixel dimensions
        return ""
    if re.match(r"^\d+_?\d+_\d+", l):  # image filenames
        return ""
    if re.search(r"(?:jpg|png|bmp|jpeg|pixel|EXIF|sRGB)", l, re.I):
        return ""
    return l

def extract_qa_from_pdf(pdf_glob):
    """Extract questions + options from PDF."""
    paths = sorted([p for p in glob.glob(pdf_glob) if p.endswith(".pdf")])
    if not paths:
        print(f"No PDF: {pdf_glob}")
        return {}, {}
    path = paths[0]
    doc = fitz.open(path)
    
    # Build full text without page separators
    lines = []
    for i in range(len(doc)):
        for line in doc[i].get_text().split("\n"):
            cleaned = clean_line(line)
            if cleaned:
                lines.append(cleaned)
    
    doc.close()
    
    # Parse: group lines by question number
    q_data = {}  # qnum -> {"text": [], "options": []}
    current_q = None
    q_lines = []
    
    for line in lines:
        # Check if line starts a new question: "NN." or "NN)"
        m = re.match(r"^\s*(\d{1,2})\s*[.)]\s*(.*)", line)
        if m:
            num = int(m.group(1))
            rest = m.group(2).strip()
            if 1 <= num <= 40:
                if current_q and q_lines:
                    opts = extract_options("\n".join(q_lines))
                    q_data[current_q] = {
                        "opts": [o["text"] for o in opts[:4]],
                        "raw_lines": q_lines,
                    }
                current_q = num
                q_lines = [rest] if rest else []
                continue
        
        if current_q:
            q_lines.append(line)
    
    if current_q and q_lines:
        opts = extract_options("\n".join(q_lines))
        q_data[current_q] = {
            "opts": [o["text"] for o in opts[:4]],
            "raw_lines": q_lines,
        }
    
    return q_data

# 1. Reading PDF
print("=== READING ===")
r = extract_qa_from_pdf("downloads/1.*20*")
print(f"Questions: {len(r)}")
for qnum in sorted(r)[:5]:
    opts = r[qnum]["opts"]
    safe = (opts[0][:50] if opts else "NONE").encode("ascii", errors="replace").decode("ascii")
    print(f"  Q{qnum:02d}: {len(opts)} opts -> {safe}")

# 2. Listening PDF  
print("\n=== LISTENING ===")
l = extract_qa_from_pdf("downloads/3.*20*")
print(f"Questions: {len(l)}")
for qnum in sorted(l)[:5]:
    opts = l[qnum]["opts"]
    safe = (opts[0][:50] if opts else "NONE").encode("ascii", errors="replace").decode("ascii")
    print(f"  Q{qnum:02d}: {len(opts)} opts -> {safe}")

# 3. Update DB
print("\n=== UPDATING ===")
updated = 0

for qnum, data in sorted(r.items()):
    opts = data["opts"]
    raw = data["raw_lines"]
    update = {"pilihan_a": "", "pilihan_b": "", "pilihan_c": "", "pilihan_d": ""}
    # Get question text from first few lines
    question_text = ""
    for line in raw:
        if line and not re.match(r"^[\u2460-\u2463]", line):
            question_text = line[:2000]
            break
    if question_text:
        update["teks_soal"] = question_text
    if len(opts) >= 2:
        update["pilihan_a"] = opts[0][:500]
        update["pilihan_b"] = opts[1][:500]
        update["pilihan_c"] = opts[2][:500] if len(opts) > 2 else ""
        update["pilihan_d"] = opts[3][:500] if len(opts) > 3 else ""
    if update.get("teks_soal") or any(update.get(k) for k in ["pilihan_a","pilihan_b"]):
        supa.table("soal_eps").update(update).eq("sumber", "open_test").eq("tahun_soal", YEAR).eq("nomor_asli", qnum).execute()
        updated += 1
    if qnum == 38:
        safe = question_text.encode("ascii", errors="replace").decode("ascii") if question_text else "NONE"
        print(f"  Q38: text={safe[:100]} opts={len(opts)}")

for qnum, data in sorted(l.items()):
    opts = data["opts"]
    raw = data["raw_lines"]
    update = {"pilihan_a": "", "pilihan_b": "", "pilihan_c": "", "pilihan_d": ""}
    question_text = ""
    for line in raw:
        line_c = clean_line(line)
        if line_c and not re.match(r"^[\u2460-\u2463]", line_c):
            question_text = line_c[:2000]
            break
    if question_text:
        update["teks_soal"] = question_text
    if len(opts) >= 2:
        update["pilihan_a"] = opts[0][:500]
        update["pilihan_b"] = opts[1][:500]
        update["pilihan_c"] = opts[2][:500] if len(opts) > 2 else ""
        update["pilihan_d"] = opts[3][:500] if len(opts) > 3 else ""
    if update.get("teks_soal") or any(update.get(k) for k in ["pilihan_a","pilihan_b"]):
        supa.table("soal_eps").update(update).eq("sumber", "open_test").eq("tahun_soal", YEAR).eq("nomor_asli", qnum).execute()
        updated += 1

print(f"Updated: {updated}/40")

# 4. Show sample Q38
if 38 in r:
    print(f"\nQ38 options: {r[38]['opts']}")
elif 38 in l:
    print(f"\nQ38 options: {l[38]['opts']}")
else:
    print("\nQ38 not found in either PDF")
    # Try looking directly
    paths = [p for p in sorted(glob.glob("downloads/3.*20*.pdf")) if p.endswith(".pdf")]
    if paths:
        doc = fitz.open(paths[0])
        for i in range(len(doc)):
            text = doc[i].get_text()
            if "38" in text:
                safe = text[:500].encode("ascii", errors="replace").decode("ascii")
                print(f"  Page {i+1} text: {safe[:200]}")
        doc.close()
