#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix konversi jawaban:
1. Reading: Cari teks jawaban di pilihan_a/b/c/d -> konversi ke a/b/c/d
2. Listening: Ekstrak jawaban yang benar dari appendix-answers.pdf
   (biasanya format: 1. ② atau (2) ① dll)
"""

import json
import re
from datetime import datetime
from pathlib import Path

import fitz

print("=== FIX KONVERSI JAWABAN ===\n")

base_dir = Path("../assets/langit-korea-extracted")
pdf_path = Path("../pdf_modul/appendix-answers.pdf")

# Buka PDF
try:
    doc = fitz.open(str(pdf_path))
    print(f"✓ PDF berhasil dibuka: {len(doc)} halaman\n")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Pola untuk ekstrak jawaban listening yang benar
# Di PDF biasanya: "1. ②" atau "(1) ①" dll
jawaban_listening_pattern = re.compile(r"^(\d+)\.\s*[①②③④]", re.MULTILINE)

# Dictionary untuk menyimpan jawaban listening per unit
jawaban_listening = {}

# Parse PDF untuk jawaban listening
current_unit = None
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Cek nomor unit (2 digit)
        if re.match(r"^\d{2}$", line):
            unit_num = int(line)
            if 31 <= unit_num <= 60:
                current_unit = unit_num
                if current_unit not in jawaban_listening:
                    jawaban_listening[current_unit] = {}
            continue

        if not current_unit:
            continue

        # Cek pola jawaban listening: "1. ②"
        match = re.match(r"^(\d+)\.\s*([①②③④])", line)
        if match:
            nomor = int(match.group(1))
            jawaban_symbol = match.group(2)
            # Konversi ke a/b/c/d
            mapping = {"①": "a", "②": "b", "③": "c", "④": "d"}
            jawaban_listening[current_unit][nomor] = mapping[jawaban_symbol]

doc.close()

print(f"✓ Ekstraksi jawaban listening selesai: {len(jawaban_listening)} unit")

# Sekarang update listening_data.json dengan jawaban yang benar
print("\n=== UPDATE LISTENING DATA ===\n")

updated_listening = 0
failed_units = []

for unit_num in range(31, 61):
    unit_dir = base_dir / f"unit_{unit_num:02d}"
    listening_path = unit_dir / "listening_data.json"

    if not listening_path.exists():
        failed_units.append(unit_num)
        continue

    try:
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✗ Error baca - {e}")
        failed_units.append(unit_num)
        continue

    soal_list = data.get("soal", [])
    updated = 0

    if unit_num in jawaban_listening:
        jawaban_unit = jawaban_listening[unit_num]

        for soal in soal_list:
            nomor = soal.get("nomor")
            if nomor in jawaban_unit:
                soal["jawaban"] = jawaban_unit[nomor]
                updated += 1

    # Save jika ada yang diupdate
    if updated > 0:
        try:
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✓ ({updated} soal)")
            updated_listening += updated
        except Exception as e:
            print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✗ Error simpan - {e}")
            failed_units.append(unit_num)
    else:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ⚠️  Tidak ada jawaban")

# Sekarang fix reading_data.json
print("\n=== UPDATE READING DATA ===\n")

updated_reading = 0

for unit_num in range(31, 61):
    unit_dir = base_dir / f"unit_{unit_num:02d}"
    reading_path = unit_dir / "reading_data.json"

    if not reading_path.exists():
        continue

    try:
        with open(reading_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✗ Error baca - {e}")
        continue

    soal_list = data.get("soal", [])
    updated = 0

    for soal in soal_list:
        jawaban_text = soal.get("jawaban", "").strip()
        if not jawaban_text:
            continue

        # Cek apakah jawaban_text ada di pilihan
        if jawaban_text in soal.get("pilihan_a", ""):
            soal["jawaban"] = "a"
            updated += 1
        elif jawaban_text in soal.get("pilihan_b", ""):
            soal["jawaban"] = "b"
            updated += 1
        elif jawaban_text in soal.get("pilihan_c", ""):
            soal["jawaban"] = "c"
            updated += 1
        elif jawaban_text in soal.get("pilihan_d", ""):
            soal["jawaban"] = "d"
            updated += 1
        else:
            # Mungkin sudah a/b/c/d
            if jawaban_text.lower() in ["a", "b", "c", "d"]:
                soal["jawaban"] = jawaban_text.lower()
                updated += 1

    if updated > 0:
        try:
            with open(reading_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✓ ({updated} soal)")
            updated_reading += updated
        except Exception as e:
            print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✗ Error simpan - {e}")

print(f"\n=== LAPORAN AKHIR ===")
print(f"Reading diupdate: {updated_reading} soal")
print(f"Listening diupdate: {updated_listening} soal")
print(f"Unit gagal: {len(failed_units)}")
if failed_units:
    print(f"  Detail: {failed_units}")

# Verifikasi Unit 31
print("\n=== VERIFIKASI UNIT 31 ===")

# Reading
reading_path = base_dir / "unit_31" / "reading_data.json"
with open(reading_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Reading (5 soal):")
for soal in data["soal"]:
    print(f"  Soal {soal['nomor']}: jawaban='{soal.get('jawaban', '')}'")

# Listening
listening_path = base_dir / "unit_31" / "listening_data.json"
with open(listening_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("\nListening (5 soal):")
for soal in data["soal"]:
    print(f"  Soal {soal['nomor']}: jawaban='{soal.get('jawaban', '')}'")

print("\n=== SELESAI ===")
print("Semua jawaban sudah dalam format a/b/c/d!")
print("Langkah selanjutnya: Upload ke Supabase!")
