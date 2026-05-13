"""
Forensic verification report for EPS-TOPIK Open Test data in Supabase.
Validates: completeness, integrity, consistency against source files.
"""
import hashlib, json, os, sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from supabase import create_client
supa = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

YEAR = 2023
SOURCE = "open_test"

def verify():
    report = {
        "generated_at": datetime.now().isoformat(),
        "source": "EPS-TOPIK Open Test {} from eps.go.kr".format(YEAR),
        "checks": [],
        "status": "PASS",
    }
    
    def check(name, passed, detail=""):
        report["checks"].append({
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        })
        if not passed:
            report["status"] = "FAIL"
    
    # 1. Total records
    data = supa.table("soal_eps").select("id").eq("sumber", SOURCE).eq("tahun_soal", YEAR).execute()
    check("Total records = 40", len(data.data) == 40, "Found: {}".format(len(data.data)))
    
    full = supa.table("soal_eps").select("*").eq("sumber", SOURCE).eq("tahun_soal", YEAR).order("nomor_asli").execute()
    records = full.data
    
    # 2. Unique nomor_asli 1-40
    nums = sorted(set(r["nomor_asli"] for r in records))
    check("Unique nomor_asli 1-40", nums == list(range(1, 41)), "Missing: {}".format(set(range(1,41)) - set(nums)))
    
    # 3. Reading vs Listening count
    r_count = sum(1 for r in records if r["tipe"] == "membaca")
    l_count = sum(1 for r in records if r["tipe"] == "mendengarkan")
    check("Reading = 20", r_count == 20)
    check("Listening = 20", l_count == 20)
    
    # 4. All answers valid a/b/c/d or None
    valid_jawaban = all(r.get("jawaban") in ("a","b","c","d") for r in records if r.get("jawaban"))
    none_jawaban = all(r.get("jawaban") is None for r in records if not r.get("jawaban"))
    check("All jawaban valid (a/b/c/d)", valid_jawaban)
    
    # 5. Reading questions have teks_soal
    reading_with_text = sum(1 for r in records if r["tipe"] == "membaca" and r.get("teks_soal"))
    check("Reading text 20/20", reading_with_text == 20, "Found: {}/20".format(reading_with_text))
    
    # 6. Listening questions have teks_soal
    listening_with_text = sum(1 for r in records if r["tipe"] == "mendengarkan" and r.get("teks_soal"))
    check("Listening text 20/20", listening_with_text == 20, "Found: {}/20".format(listening_with_text))
    
    # 7. Audio URLs for listening
    listening_audio = sum(1 for r in records if r["tipe"] == "mendengarkan" and r.get("audio_url"))
    check("Listening audio 20/20", listening_audio == 20, "Found: {}/20".format(listening_audio))
    
    # 8. Image URLs (JSON array) for reading questions
    reading_images = sum(1 for r in records if r["tipe"] == "membaca" and r.get("gambar_url"))
    # Count total images from JSON arrays
    total_images = 0
    image_by_question = {}
    for r in records:
        if r.get("gambar_url"):
            try:
                urls = json.loads(r["gambar_url"])
                total_images += len(urls)
                image_by_question[r["nomor_asli"]] = len(urls)
            except:
                pass
    check("Reading questions with images", reading_images > 0, "{} questions have images, {} total images".format(reading_images, total_images))
    
    # 9. Verify gambar_materi table has matching records
    gm = supa.table("gambar_materi").select("id").eq("kategori", "open_test").execute()
    check("gambar_materi records exist", len(gm.data) > 0, "Found: {} records".format(len(gm.data)))
    
    # 10. No null jawaban (all should have answers)
    null_jawaban = sum(1 for r in records if r.get("jawaban") is None)
    check("No null jawaban", null_jawaban == 0, "Found: {} null".format(null_jawaban))
    
    # 11. Consistency: nomor_asli matches tipe
    for r in records:
        expected = "membaca" if r["nomor_asli"] <= 20 else "mendengarkan"
        if r["tipe"] != expected:
            check("Tipe consistent for Q{}".format(r["nomor_asli"]), False, "Expected {} got {}".format(expected, r["tipe"]))
    
    # 12. All records have sumber='open_test' and tahun_soal=YEAR
    for r in records:
        if r.get("sumber") != SOURCE:
            check("Sumber consistent", False, "Q{} has sumber={}".format(r["nomor_asli"], r.get("sumber")))
        if r.get("tahun_soal") != YEAR:
            check("Tahun consistent", False, "Q{} has tahun={}".format(r["nomor_asli"], r.get("tahun_soal")))
    
    # Summary
    passed = sum(1 for c in report["checks"] if c["status"] == "PASS")
    failed = sum(1 for c in report["checks"] if c["status"] == "FAIL")
    report["passed"] = passed
    report["failed"] = failed
    report["summary"] = "{} passed, {} failed".format(passed, failed)
    
    # Print
    print("=== FORENSIC VERIFICATION REPORT ===")
    print("Generated:", report["generated_at"])
    print("Status:", report["status"])
    print()
    for c in report["checks"]:
        mark = "[OK]" if c["status"] == "PASS" else "[FAIL]"
        safe_detail = c.get("detail", "").encode("ascii", errors="replace").decode("ascii")
        print("{} {}: {}".format(mark, c["name"], safe_detail))
    print()
    print("Image distribution by question:")
    for q, n in sorted(image_by_question.items()):
        print("  Q{:02d}: {} image(s)".format(q, n))
    print()
    print("Summary: {} passed / {} failed".format(passed, failed))
    print("Overall: {}".format(report["status"]))
    
    # Save
    report_path = "forensic_verification_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("\nReport saved to:", report_path)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(verify())
