#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script FINAL untuk ekstraksi 5 soal listening per unit
Hanya ambil soal SEBELUM bagian skrip audio
"""

import json
import os
import re
import time
import glob
from pathlib import Path

try:
    import fitz  # PyMuPDF
    from supabase import create_client
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: {e}")
    exit(1)

load_dotenv()
PDF_FOLDER = Path("pdf_modul")
EXTRACTED_DIR = Path("assets/langit-korea-extracted")
OUTPUT_JSON = "soal_listening_final.json"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("SUPABASE_URL atau SUPABASE_ANON_KEY tidak ditemukan")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
print("Koneksi Supabase OK\n")

def parse_listening_only(text, unit_num):
    """
    Parse HANYA 5 soal listening PERTAMA
    Berhenti jika menemukan pola skrip (여 : atau 남 :)
    """
    soal_list = []
    lines = text.split('\n')
    
    current_soal = None
    current_number = None
    soal_count = 0
    
    for line in lines:
        line_stripped = line.strip()
        
        # DETEKSI AWAL SKRIP: jika ada "여 :" atau "남 :", STOP!
        if '여' in line and ':' in line:
            break
        if '남' in line and ':' in line:
            break
        
        # Deteksi nomor soal (1. 2. 3. 4. 5.)
        match = re.match(r'^(\d+)\.\s*$', line_stripped)
        if match:
            nomor = int(match.group(1))
            
            # Jika sudah 5 soal, stop
            if soal_count >= 5:
                break
            
            # Simpan soal sebelumnya
            if current_soal and current_number:
                soal_list.append(current_soal)
                soal_count += 1
            
            current_number = nomor
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
                "akses": "free" if unit_num <= 18 else "premium"
            }
            continue
        
        # Deteksi teks soal
        if current_soal and not current_soal["teks_soal"]:
            if line_stripped and not line_stripped.startswith(('①', '②', '③', '④')):
                current_soal["teks_soal"] = line_stripped
                continue
        
        # Deteksi pilihan jawaban
        if line_stripped.startswith('①'):
            current_soal["pilihan_a"] = line_stripped[1:].strip()
        elif line_stripped.startswith('②'):
            current_soal["pilihan_b"] = line_stripped[1:].strip()
        elif line_stripped.startswith('③'):
            current_soal["pilihan_c"] = line_stripped[1:].strip()
        elif line_stripped.startswith('④'):
            current_soal["pilihan_d"] = line_stripped[1:].strip()
    
    # Simpan soal terakhir
    if current_soal and current_number and soal_count < 5:
        soal_list.append(current_soal)
        soal_count += 1
    
    return soal_list[:5]

def load_jawaban():
    jawaban_path = EXTRACTED_DIR / "jawaban_all.json"
    if jawaban_path.exists():
        with open(str(jawaban_path), 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def main():
    print("=" * 60)
    print("EKSTRAKSI 5 SOAL LISTENING PER UNIT (FINAL V4)")
    print("=" * 60)
    
    jawaban_data = load_jawaban()
    print(f"Jawaban: {len(jawaban_data)} unit\n")
    
    all_soal = []
    total_uploaded = 0
    
    for unit_num in range(31, 61):
        pdf_pattern = str(PDF_FOLDER / f"unit_{unit_num:02d}_*.pdf")
        pdf_files = glob.glob(pdf_pattern)
        
        if not pdf_files:
            print(f"Unit {unit_num}: PDF tidak ditemukan")
            continue
        
        pdf_path = pdf_files[0]
        
        # Extract teks dari halaman 9
        try:
            doc = fitz.open(pdf_path)
            page = doc[8]
            text = page.get_text()
            doc.close()
        except Exception as e:
            print(f"Unit {unit_num}: Error - {e}")
            continue
        
        # Parse HANYA 5 soal pertama
        soal_list = parse_listening_only(text, unit_num)
        
        # Update jawaban
        mendengarkan_jawaban = jawaban_data.get(str(unit_num), {}).get("mendengarkan", {})
        for soal in soal_list:
            nomor = soal["nomor"]
            if str(nomor) in mendengarkan_jawaban:
                soal["jawaban"] = mendengarkan_jawaban[str(nomor)]
        
        print(f"Unit {unit_num}: {len(soal_list)} soal")
        all_soal.extend(soal_list)
    
    # Simpan ke JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_soal, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {len(all_soal)} soal listening (30 unit x 5 soal)")
    print(f"File: {OUTPUT_JSON}")
    print("=" * 60)

if __name__ == "__main__":
    main()
