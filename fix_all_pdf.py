"""Extract questions+options from PDF files and update database."""
import sys, glob, re, os
sys.path.insert(0, "epstopik_forensic_scraper")
from scraper.parsing_rules import extract_options, is_question_start, split_listening_items
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

supa = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
YEAR = 2023
import fitz

def extract_blocks_from_pdf(pdf_glob):
    """Extract text blocks with positions from PDF."""
    paths = sorted([p for p in glob.glob(pdf_glob) if p.endswith(".pdf")])
    if not paths:
        print(f"No PDF files matching: {pdf_glob}")
        return []
    path = paths[0]
    print(f"Processing: {path.split(os.sep)[-1].encode('ascii',errors='replace').decode('ascii')}")
    doc = fitz.open(path)
    blocks = []
    for i in range(len(doc)):
        page = doc[i]
        pd = page.get_text("dict")
        for b in pd.get("blocks", []):
            if b["type"] == 0:
                for line in b.get("lines", []):
                    t = "".join(s["text"] for s in line.get("spans", []))
                    if t.strip():
                        bb = line["bbox"]
                        blocks.append({
                            "text": t.strip(), "page": i+1,
                            "y0": round(bb[1], 1), "x0": round(bb[0], 1)
                        })
    doc.close()
    print(f"  {len(blocks)} text blocks")
    return blocks

def assign_options_to_questions(blocks, q_start=1, q_end=40):
    """Extract options from blocks and assign to questions based on position."""
    # Find question boundaries
    q_boundaries = []
    for b in blocks:
        is_q, qnum = is_question_start(b["text"])
        if is_q and q_start <= qnum <= q_end:
            q_boundaries.append((qnum, b["y0"], b))
    
    # Sort by y-position (vertical order on page)
    q_boundaries.sort(key=lambda x: (x[1]))
    
    # Assign options to each question
    q_options = {}  
    
    for i, (qnum, q_y0, q_block) in enumerate(q_boundaries):
        # Get blocks from this question until the next question or end
        next_y = q_boundaries[i+1][1] if i+1 < len(q_boundaries) else float('inf')
        question_text_parts = [q_block["text"]]
        opts = []
        
        for b in blocks:
            if b["page"] == q_block["page"] and q_y0 <= b["y0"] < next_y and b is not q_block:
                t = b["text"]
                question_text_parts.append(t)
                found_opts = extract_options(t)
                if found_opts:
                    opts.extend(found_opts)
        
        # Clean option text
        clean_opts = []
        for o in opts:
            text = o["text"].strip().rstrip("|").rstrip("-").strip()
            if text:
                clean_opts.append(text[:500])
        
        # Get the question text (remove the number prefix)
        qt = " ".join(question_text_parts)
        m = re.match(r"^\s*\d{1,2}\s*[\.\s\)]\s*(.*)", qt, re.DOTALL)
        question_text = m.group(1).strip() if m else qt
        
        q_options[qnum] = {
            "text": question_text[:2000],
            "opts": clean_opts[:4],
        }
    
    return q_options

# 1. Process Reading PDF (Q1-Q20)
print("=" * 50)
print("READING PDF")
print("=" * 50)
r_blocks = extract_blocks_from_pdf("downloads/1.*20*")
r_data = assign_options_to_questions(r_blocks, 1, 20)

# 2. Process Listening PDF (Q21-Q40)
print("=" * 50)
print("LISTENING PDF")
print("=" * 50)
l_blocks = extract_blocks_from_pdf("downloads/3.*20*")
l_data = assign_options_to_questions(l_blocks, 21, 40)

# 3. Update database
print("=" * 50)
print("UPDATING DATABASE")
print("=" * 50)
updated = 0

for qnum in sorted(r_data):
    d = r_data[qnum]
    opts = d["opts"]
    qt = d["text"]
    
    row = {}
    if qt:
        row["teks_soal"] = qt
    if len(opts) >= 2:
        row["pilihan_a"] = opts[0]
        row["pilihan_b"] = opts[1]
        row["pilihan_c"] = opts[2] if len(opts) > 2 else ""
        row["pilihan_d"] = opts[3] if len(opts) > 3 else ""
    
    if row:
        supa.table("soal_eps").update(row).eq("sumber", "open_test").eq("tahun_soal", YEAR).eq("nomor_asli", qnum).execute()
        updated += 1
        safe = (qt[:40] if qt else "?").encode("ascii", errors="replace").decode("ascii")
        print(f"  Q{qnum:02d}: text={safe} opts={len(opts)}")

for qnum in sorted(l_data):
    d = l_data[qnum]
    opts = d["opts"]
    qt = d["text"]
    
    # For listening, if no question text, add instruction
    if not qt or len(qt) < 5:
        qt = f"Putar audio untuk soal nomor {qnum}, lalu pilih jawaban yang tepat."
    
    row = {"teks_soal": qt}
    if len(opts) >= 2:
        row["pilihan_a"] = opts[0]
        row["pilihan_b"] = opts[1]
        row["pilihan_c"] = opts[2] if len(opts) > 2 else ""
        row["pilihan_d"] = opts[3] if len(opts) > 3 else ""
    else:
        # Create generic options for listening
        row["pilihan_a"] = "①"
        row["pilihan_b"] = "②"
        row["pilihan_c"] = "③"
        row["pilihan_d"] = "④"
    
    supa.table("soal_eps").update(row).eq("sumber", "open_test").eq("tahun_soal", YEAR).eq("nomor_asli", qnum).execute()
    updated += 1
    print(f"  Q{qnum:02d}: text={qt[:40]} opts={len(opts)}")

print(f"\nUpdated: {updated}/40 questions")
print("Done!")
