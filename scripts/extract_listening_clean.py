#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk ekstraksi soal listening dari PDF EPS-TOPIK
dan mengintegrasikannya ke Supabase
"""

import glob
import json
import os
import re
import time
from pathlib import Path

try:
    import fitz  # PyMuPDF
    from dotenv import load_dotenv
    from supabase import create_client
except ImportError as e:
    print(f"Error: {e}")
    print("Jalankan: pip install pymupdf supabase-py python-dotenv")
    exit(1)

# Load environment variables
load_dotenv()

# Konfigurasi
PDF_FOLDER = Path("pdf_modul")
EXTRACTED_DIR = Path("assets/langit-korea-extracted")
OUTPUT_JSON = "soal_listening.json"

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("SUPABASE_URL atau SUPABASE_ANON_KEY tidak ditemukan di .env")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
print("Koneksi Supabase OK")


def extract_listening_from_pdf(pdf_path, unit_num):
    """Extract soal listening dari halaman 9 (index 8) PDF"""
    try:
        doc = fitz.open(pdf_path)
        page = doc[8]  # Halaman 9 (index 8)
        text = page.get_text()
        doc.close()
        return parse_listening_text(text, unit_num)
    except Exception as e:
        print(f"Error membaca {pdf_path}: {e}")
        return []


def parse_listening_text(text, unit_num):
    """Parse teks listening menjadi soal-soal terstruktur"""
    soal_list = []
    lines = text.split("\n")

    current_soal = None
    current_number = None

    for line in lines:
        line = line.strip()

        # Deteksi nomor soal (1. 2. 3. 4. 5.)
        match = re.match(r"^(\d+)\.\s*$", line)
        if match:
            # Simpan soal sebelumnya jika ada
            if current_soal and current_number:
                soal_list.append(current_soal)

            current_number = int(match.group(1))
            current_soal = {
                "id": f"u{unit_num}_l{current_number}",
                "unit": unit_num,
                "nomor": current_number,
                "tipe": "mendengarkan",
                "teks_soal": "",
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
                "jawaban": "",
                "audio_teks": "",
                "ada_gambar_pilihan": False,
                "gambar_pilihan": {},
                "akses": "free" if unit_num <= 18 else "premium",
            }
            continue

        # Deteksi teks soal
        if current_soal and not current_soal["teks_soal"]:
            if line and not line.startswith(("①", "②", "③", "④")):
                current_soal["teks_soal"] = line
                continue

        # Deteksi pilihan jawaban
        if line.startswith("①"):
            current_soal["pilihan_a"] = line[1:].strip()
        elif line.startswith("②"):
            current_soal["pilihan_b"] = line[1:].strip()
        elif line.startswith("③"):
            current_soal["pilihan_c"] = line[1:].strip()
        elif line.startswith("④"):
            current_soal["pilihan_d"] = line[1:].strip()

    # Simpan soal terakhir
    if current_soal and current_number:
        soal_list.append(current_soal)

    return soal_list


def load_jawaban():
    """Load kunci jawaban dari jawaban_all.json"""
    jawaban_path = EXTRACTED_DIR / "jawaban_all.json"
    if jawaban_path.exists():
        with open(str(jawaban_path), "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_skrip():
    """Load skrip audio dari skrip_all.json"""
    skrip_path = EXTRACTED_DIR / "skrip_all.json"
    if skrip_path.exists():
        with open(str(skrip_path), "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    print("=" * 60)
    print("EKSTRAKSI SOAL LISTENING EPS-TOPIK")
    print("=" * 60)

    # Load jawaban dan skrip
    print("\nLoading jawaban dan skrip...")
    jawaban_data = load_jawaban()
    skrip_data = load_skrip()
    print(f"  Jawaban: {len(jawaban_data)} unit")
    print(f"  Skrip: {len(skrip_data)} unit")

    all_listening_soal = []
    total_uploaded = 0

    # Process units 31-60
    for unit_num in range(31, 61):
        # Cari file PDF yang sesuai
        pdf_pattern = str(PDF_FOLDER / f"unit_{unit_num:02d}_*.pdf")
        pdf_files = glob.glob(pdf_pattern)

        if not pdf_files:
            print(f"\nUnit {unit_num}: PDF tidak ditemukan, skip")
            continue

        pdf_path = pdf_files[0]
        print(f"\nUnit {unit_num}: {Path(pdf_path).name}")

        # Extract soal listening dari PDF
        listening_soal = extract_listening_from_pdf(pdf_path, unit_num)

        if not listening_soal:
            print("  Tidak ada soal listening yang ditemukan")
            continue

        print(f"  {len(listening_soal)} soal listening ditemukan")

        # Update dengan jawaban
        mendengarkan_jawaban = jawaban_data.get(str(unit_num), {}).get(
            "mendengarkan", {}
        )
        unit_skrip = skrip_data.get(str(unit_num), {})

        for soal in listening_soal:
            nomor = soal["nomor"]
            if str(nomor) in mendengarkan_jawaban:
                soal["jawaban"] = mendengarkan_jawaban[str(nomor)]
            if str(nomor) in unit_skrip:
                soal["audio_teks"] = unit_skrip[str(nomor)]

        # Upload ke Supabase
        uploaded = 0
        for soal in listening_soal:
            # Bersihkan teks
            for key in [
                "teks_soal",
                "pilihan_a",
                "pilihan_b",
                "pilihan_c",
                "pilihan_d",
                "audio_teks",
            ]:
                if key in soal:
                    soal[key] = re.sub(
                        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(soal[key])
                    )
                    soal[key] = re.sub(r"\s+", " ", soal[key]).strip()

            # Pastikan jawaban valid
            if soal.get("jawaban") not in ["a", "b", "c", "d"]:
                continue

            # Siapkan row untuk Supabase
            row = {
                "unit": soal["unit"],
                "tipe": "mendengarkan",
                "teks_soal": soal["teks_soal"],
                "pilihan_a": soal["pilihan_a"],
                "pilihan_b": soal["pilihan_b"],
                "pilihan_c": soal["pilihan_c"],
                "pilihan_d": soal["pilihan_d"],
                "jawaban": soal["jawaban"],
                "audio_teks": soal["audio_teks"],
                "ada_gambar_pilihan": soal["ada_gambar_pilihan"],
                "akses": soal["akses"],
            }

            try:
                client.table("soal_eps").upsert(row).execute()
                uploaded += 1
                time.sleep(0.03)  # Rate limiting
            except Exception as e:
                print(f"  Error upload {soal['id']}: {str(e)[:80]}")

        total_uploaded += uploaded
        print(f"  {uploaded} soal berhasil diupload ke Supabase")
        all_listening_soal.extend(listening_soal)

    # Simpan ke JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_listening_soal, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("LAPORAN EKSTRAKSI LISTENING")
    print("=" * 60)
    print(f"Total soal listening: {len(all_listening_soal)}")
    print(f"Total diupload ke Supabase: {total_uploaded}")
    print(f"Data tersimpan di: {OUTPUT_JSON}")
    print("=" * 60)


if __name__ == "__main__":
    main()
