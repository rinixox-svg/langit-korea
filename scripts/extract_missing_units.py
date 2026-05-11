#!/usr/bin/env python3
import fitz, json, re, os
from pathlib import Path

EXTRACTED_DIR = Path("../assets/langit-korea-extracted")

def extract_hal9_from_pdf(pdf_path, unit_num):
    """Extract teks dari halaman 9 PDF dan simpan ke hal9_soal.txt"""
    try:
        doc = fitz.open(pdf_path)
        page = doc[8]  # Halaman 9 (index 8)
        text = page.get_text()
        doc.close()
        
        # Buat folder jika belum ada
        txt_dir = EXTRACTED_DIR / f"unit_{unit_num:02d}" / "teks"
        txt_dir.mkdir(parents=True, exist_ok=True)
        
        # Simpan ke hal9_soal.txt
        txt_path = txt_dir / "hal9_soal.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Unit {unit_num}: hal9_soal.txt created")
        return True
    except Exception as e:
        print(f"Unit {unit_num}: Error - {e}")
        return False

# Process unit 46, 56, 58
missing_units = [46, 56, 58]
pdf_folder = Path("../pdf_modul")

for unit_num in missing_units:
    # Cari file PDF
    pdf_pattern = str(pdf_folder / f"unit_{unit_num:02d}_*.pdf")
    import glob
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"Unit {unit_num}: PDF tidak ditemukan")
        continue
    
    extract_hal9_from_pdf(pdf_files[0], unit_num)

print("\nDone!")
