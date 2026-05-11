#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ekstrak halaman 8 (soal reading) dari PDF unit 46, 56, 58
yang sebelumnya terlewat saat proses ekstraksi awal.
"""

import re
from pathlib import Path

import fitz

print("=== EKSTRAKSI HALAMAN 8 UNTUK UNIT 46, 56, 58 ===\n")

pdf_dir = Path("../pdf_modul")
base_dir = Path("../assets/langit-korea-extracted")

# Mapping unit ke file PDF
units_to_fix = {
    46: "unit_46_animal_husbry.pdf",
    56: "unit_56_industrial_accidents_first_ai.pdf",
    58: "unit_58_labor_stards_act.pdf",  # Note: nama file mungkin berbeda
}

# Coba cari nama file yang benar untuk unit 58
if not (pdf_dir / units_to_fix[58]).exists():
    # Cari file yang mirip
    for f in pdf_dir.iterdir():
        if "58" in f.name and "labor" in f.name.lower():
            units_to_fix[58] = f.name
            break

for unit_num, pdf_name in units_to_fix.items():
    print(f"[{unit_num}] Memproses {pdf_name}...")

    pdf_path = pdf_dir / pdf_name
    if not pdf_path.exists():
        print(f"  ✗ File tidak ditemukan: {pdf_path}")
        continue

    try:
        doc = fitz.open(str(pdf_path))

        # Halaman 8 adalah index 7 (0-based)
        if len(doc) < 8:
            print(f"  ✗ PDF hanya punya {len(doc)} halaman")
            doc.close()
            continue

        page = doc[7]  # Halaman 8
        text = page.get_text()

        # Simpan ke teks/hal8_soal.txt
        unit_dir = base_dir / f"unit_{unit_num:02d}" / "teks"
        unit_dir.mkdir(parents=True, exist_ok=True)

        output_path = unit_dir / "hal8_soal.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"  ✓ Tersimpan: {output_path}")
        print(f"    Isi (100 chars): {text[:100].replace(chr(10), ' ')}...")

        doc.close()

    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n=== SELESAI ===")
print("Silahkan jalankan kembali script parsing untuk membuat reading_data.json")
