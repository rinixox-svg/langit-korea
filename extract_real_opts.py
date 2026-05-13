"""Extract REAL options from PDF files using fixed parsing_rules."""
import sys, glob, re, os
sys.path.insert(0, "epstopik_forensic_scraper")
from scraper.parsing_rules import extract_options, is_question_start
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

supa = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
YEAR = 2023
import fitz

def extract_options_from_pdf(pdf_glob):
    """Extract ALL option text directly from PDF page text."""
    paths = sorted([p for p in glob.glob(pdf_glob) if p.endswith(".pdf")])
    if not paths:
        return {}
    path = paths[0]
    doc = fitz.open(path)
    full_text = ""
    for i in range(len(doc)):
        full_text += doc[i].get_text() + "\n---PAGE---\n"
    doc.close()
    
    # Split by question numbers to associate options with questions
    lines = full_text.split("\n")
    
    # Strategy: iterate through lines, track current question
    question_options = {}  # qnum -> [opt_texts]
    current_q = None
    buffer = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Detect question start
        m = re.match(r"^\s*(\d{1,2})\s*[.)]\s*$", stripped)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 40:
                if current_q and buffer:
                    opts = extract_options("\n".join(buffer))
                    if opts:
                        question_options[current_q] = [o["text"] for o in opts[:4]]
                current_q = num
                buffer = []
                continue
        if current_q:
            buffer.append(stripped)
    
    # Last question
    if current_q and buffer:
        opts = extract_options("\n".join(buffer))
        if opts:
            question_options[current_q] = [o["text"] for o in opts[:4]]
    
    return question_options

# 1. Reading PDF
print("=== READING PDF ===")
r_opts = extract_options_from_pdf("downloads/1.*20*")
print(f"Questions with options: {len(r_opts)}")

# 2. Listening PDF
print("=== LISTENING PDF ===")
l_opts = extract_options_from_pdf("downloads/3.*20*")
print(f"Questions with options: {len(l_opts)}")

# 3. Update database
print("=== UPDATE DB ===")
updated = 0
for qnum, opts in sorted(r_opts.items()):
    if len(opts) >= 2:
        supa.table("soal_eps").update({
            "pilihan_a": opts[0][:500],
            "pilihan_b": opts[1][:500],
            "pilihan_c": opts[2][:500] if len(opts) > 2 else "",
            "pilihan_d": opts[3][:500] if len(opts) > 3 else "",
        }).eq("sumber", "open_test").eq("tahun_soal", YEAR).eq("nomor_asli", qnum).execute()
        updated += 1
        safe = opts[0][:40].encode("ascii", errors="replace").decode("ascii")
        print(f"  Q{qnum:02d}: {safe}")

for qnum, opts in sorted(l_opts.items()):
    if len(opts) >= 2:
        supa.table("soal_eps").update({
            "pilihan_a": opts[0][:500],
            "pilihan_b": opts[1][:500],
            "pilihan_c": opts[2][:500] if len(opts) > 2 else "",
            "pilihan_d": opts[3][:500] if len(opts) > 3 else "",
        }).eq("sumber", "open_test").eq("tahun_soal", YEAR).eq("nomor_asli", qnum).execute()
        updated += 1
        safe = opts[0][:40].encode("ascii", errors="replace").decode("ascii")
        print(f"  Q{qnum:02d}: {safe}")

print(f"\nUpdated: {updated}/40 questions")
print("DONE")
