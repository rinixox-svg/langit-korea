"""Fix all questions: update text, add generic options where missing."""
from supabase import create_client
from dotenv import load_dotenv
import os, re, glob, hashlib
load_dotenv()

supa = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
YEAR = 2023

# Fetch current data
data = supa.table("soal_eps").select("*").eq("sumber", "open_test").eq("tahun_soal", YEAR).order("nomor_asli").execute()
records = data.data

print(f"Processing {len(records)} records...")
updated = 0

for r in records:
    qnum = r["nomor_asli"]
    qtype = r["tipe"]
    has_opts = bool(r.get("pilihan_a"))
    has_text = bool(r.get("teks_soal") and len(r.get("teks_soal", "")) > 5)
    
    row = {}
    
    # For listening without text, add instruction
    if qtype == "mendengarkan" and not has_text:
        row["teks_soal"] = f"Putar audio untuk soal nomor {qnum}, lalu pilih jawaban yang tepat."
    
    # For questions without options, add placeholders
    if not has_opts:
        row["pilihan_a"] = "①"
        row["pilihan_b"] = "②"
        row["pilihan_c"] = "③"
        row["pilihan_d"] = "④"
    
    if row:
        supa.table("soal_eps").update(row).eq("id", r["id"]).execute()
        updated += 1
        reasons = []
        if "teks_soal" in row: reasons.append("text")
        if "pilihan_a" in row: reasons.append("opts")
        print(f"  Q{qnum:02d} ({qtype}): updated ({', '.join(reasons)})")

total = len(records)
r_txt = len([r for r in records if r["tipe"] == "membaca" and r.get("teks_soal") and len(r.get("teks_soal","")) > 5])
l_txt = len([r for r in records if r["tipe"] == "mendengarkan" and r.get("teks_soal") and len(r.get("teks_soal","")) > 5])
r_opt = len([r for r in records if r["tipe"] == "membaca" and r.get("pilihan_a")])
l_opt = len([r for r in records if r["tipe"] == "mendengarkan" and r.get("pilihan_a")])

print(f"\n=== RESULT ===")
print(f"Updated: {updated}/{total}")
print(f"Reading text: {r_txt}/20 | Options: {r_opt}/20")
print(f"Listening text: {l_txt}/20 | Options: {l_opt}/20")
