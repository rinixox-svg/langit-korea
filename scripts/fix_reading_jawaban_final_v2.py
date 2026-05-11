#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix reading jawaban FINAL:
1. Ekstrak jawaban dari appendix-answers.pdf (format: (1), (2), (3), (4))
2. Konversi ke a/b/c/d
3. Update reading_data.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

import fitz

print("=== FIX READING JAWABAN FINAL ===\n")

base_dir = Path("../assets/langit-korea-extracted")
pdf_path = Path("../pdf_modul/appendix-answers.pdf")

# Buka PDF
try:
    doc = fitz.open(str(pdf_path))
    print(f"✓ PDF berhasil dibuka: {len(doc)} halaman\n")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Parse jawaban reading per unit
jawaban_reading = {}

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    lines = text.split("\n")

    current_unit = None
    current_section = None  # "어휘" atau "문법"
    soal_counter = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Cek nomor unit (2 digit)
        if re.match(r"^\d{2}$", line):
            unit_num = int(line)
            if 31 <= unit_num <= 60:
                current_unit = unit_num
                if current_unit not in jawaban_reading:
                    jawaban_reading[current_unit] = {}
                soal_counter = 0
            continue

        if not current_unit:
            continue

        # Cek section (어휘 atau 문법)
        if "어휘" in line:
            current_section = "reading"
            continue
        elif "문법" in line:
            current_section = "grammar"  # Skip grammar
            continue

        if current_section != "reading":
            continue

        # Cek pola jawaban: (1), (2), (3), (4) atau ⑴, ⑵, ⑶, ⑷
        match1 = re.match(r"^\(?⑴|\(?1\)?", line)
        match2 = re.match(r"^\(?⑵|\(?2\)?", line)
        match3 = re.match(r"^\(?⑶|\(?3\)?", line)
        match4 = re.match(r"^\(?⑷|\(?4\)?", line)

        if match1 or match2 or match3 or match4:
            soal_counter += 1
            nomor = soal_counter

            # Tentukan a/b/c/d
            if match1:
                jawaban_reading[current_unit][nomor] = "a"
            elif match2:
                jawaban_reading[current_unit][nomor] = "b"
            elif match3:
                jawaban_reading[current_unit][nomor] = "c"
            elif match4:
                jawaban_reading[current_unit][nomor] = "d"

doc.close()

print(f"✓ Ekstraksi selesai: {len(jawaban_reading)} unit")

# Update reading_data.json
print("\n=== UPDATE READING DATA ===\n")

updated_total = 0
failed_units = []

for unit_num in range(31, 61):
    if unit_num not in jawaban_reading:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: Tidak ada jawaban")
        failed_units.append(unit_num)
        continue

    reading_path = base_dir / f"unit_{unit_num:02d}" / "reading_data.json"

    if not reading_path.exists():
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: File tidak ada")
        failed_units.append(unit_num)
        continue

    try:
        with open(reading_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: Error baca - {e}")
        failed_units.append(unit_num)
        continue

    soal_list = data.get("soal", [])
    updated = 0

    for soal in soal_list:
        nomor = soal.get("nomor")
        if nomor in jawaban_reading[unit_num]:
            soal["jawaban"] = jawaban_reading[unit_num][nomor]
            updated += 1

    # Save
    try:
        with open(reading_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✓ ({updated} soal)")
        updated_total += updated
    except Exception as e:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: Error simpan - {e}")
        failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Total jawaban reading diupdate: {updated_total}")
print(f"Unit gagal: {len(failed_units)}")
if failed_units:
    print(f"  Detail: {failed_units}")

# Verifikasi Unit 31
print("\n=== VERIFIKASI UNIT 31 ===")
reading_path = base_dir / "unit_31" / "reading_data.json"
with open(reading_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Reading (5 soal):")
for soal in data["soal"]:
    print(f"  Soal {soal['nomor']}: jawaban='{soal.get('jawaban', '')}'")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_fix_reading_final.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "updated": updated_total,
            "gagal": failed_units,
            "detail": {k: v for k, v in jawaban_reading.items()},
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
print("Semua jawaban reading sudah dalam format a/b/c/d!")
