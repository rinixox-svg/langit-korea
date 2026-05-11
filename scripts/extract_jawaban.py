#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk ekstrak jawaban dari appendix-answers.pdf
dan mengupdate field 'jawaban' di reading_data.json dan listening_data.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF

print("=== EKSTRAKSI JAWABAN DARI APPENDIX-ANSWERS.PDF ===\n")

base_dir = Path("../assets/langit-korea-extracted")
pdf_path = Path("../pdf_modul/appendix-answers.pdf")

# Buka PDF
try:
    doc = fitz.open(str(pdf_path))
    print(f"✓ PDF berhasil dibuka: {len(doc)} halaman\n")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Pola untuk mendeteksi unit (contoh: "31", "34", dll)
unit_pattern = re.compile(r"^(\d{2})$")  # 2 digit di awal baris

# Pola untuk mendeteksi jawaban (⑴, ⑵, ⑶, ⑷ atau 1., 2., 3., 4.)
jawaban_pattern_1 = re.compile(r"^(⑴|⑵|⑶|⑷)\s*(.+)$")  # Untuk reading
jawaban_pattern_2 = re.compile(r"^(\d+)\.\s*(.+)$")  # Untuk listening

# Dictionary untuk menyimpan jawaban per unit
jawaban_per_unit = {}

# Parse semua halaman
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    lines = text.split("\n")

    current_unit = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Cek apakah ini nomor unit (2 digit)
        match_unit = unit_pattern.match(line)
        if match_unit:
            unit_num = int(match_unit.group(1))
            if 31 <= unit_num <= 60:
                current_unit = unit_num
                if current_unit not in jawaban_per_unit:
                    jawaban_per_unit[current_unit] = {
                        "reading": {},  # nomor_soal: jawaban (a/b/c/d)
                        "listening": {},
                    }
            continue

        if not current_unit:
            continue

        # Cek jawaban reading (⑴, ⑵, ⑶, ⑷)
        match_jwb = jawaban_pattern_1.match(line)
        if match_jwb:
            # Tentukan nomor soal berdasarkan urutan
            # Biasanya 5 soal per unit, jadi kita hitung
            nomor = len(jawaban_per_unit[current_unit]["reading"]) + 1
            jawaban_text = match_jwb.group(2).strip()

            # Konversi ke a/b/c/d
            # Asumsi: ⑴=1=a, ⑵=2=b, ⑶=3=c, ⑷=4=d
            # Atau bisa berupa teks seperti "지퍼를 올렸어요."
            # Untuk reading, jawaban berupa teks pilihan
            jawaban_per_unit[current_unit]["reading"][nomor] = jawaban_text
            continue

        # Cek jawaban listening (1., 2., 3., 4., 5.)
        match_jwb2 = jawaban_pattern_2.match(line)
        if match_jwb2:
            nomor = int(match_jwb2.group(1))
            jawaban_text = match_jwb2.group(2).strip()
            jawaban_per_unit[current_unit]["listening"][nomor] = jawaban_text
            continue

# Tutup PDF
doc.close()

print(f"✓ Ekstraksi selesai. Ditemukan jawaban untuk {len(jawaban_per_unit)} unit.\n")

# Sekarang update reading_data.json dan listening_data.json
print("=== MENGUPDATE FILE JSON ===\n")

updated_reading = 0
updated_listening = 0
failed_units = []

for unit_num in range(31, 61):
    if unit_num not in jawaban_per_unit:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: Tidak ada jawaban di PDF")
        failed_units.append(unit_num)
        continue

    unit_dir = base_dir / f"unit_{unit_num:02d}"
    jawaban = jawaban_per_unit[unit_num]

    # Update reading_data.json
    reading_path = unit_dir / "reading_data.json"
    if reading_path.exists():
        try:
            with open(reading_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            soal_list = data.get("soal", [])
            updated = 0

            for soal in soal_list:
                nomor = soal.get("nomor")
                if nomor in jawaban["reading"]:
                    # Cari jawaban yang sesuai (a/b/c/d)
                    jwb_text = jawaban["reading"][nomor]

                    # Cek apakah jwb_text adalah teks pilihan
                    # Jika ya, cari di pilihan_a/b/c/d
                    if jwb_text in soal.get("pilihan_a", ""):
                        soal["jawaban"] = "a"
                    elif jwb_text in soal.get("pilihan_b", ""):
                        soal["jawaban"] = "b"
                    elif jwb_text in soal.get("pilihan_c", ""):
                        soal["jawaban"] = "c"
                    elif jwb_text in soal.get("pilihan_d", ""):
                        soal["jawaban"] = "d"
                    else:
                        # Mungkin formatnya berbeda, simpan sebagai teks
                        soal["jawaban"] = jwb_text
                    updated += 1

            # Save
            with open(reading_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            if updated > 0:
                updated_reading += updated
                print(
                    f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✓ Reading ({updated} soal)"
                )
            else:
                print(
                    f"[{unit_num - 30}/30] Unit {unit_num:02d}: ⚠️  Reading (tidak ada yang diupdate)"
                )

        except Exception as e:
            print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✗ Reading - {e}")
            failed_units.append(unit_num)

    # Update listening_data.json
    listening_path = unit_dir / "listening_data.json"
    if listening_path.exists():
        try:
            with open(listening_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            soal_list = data.get("soal", [])
            updated = 0

            for soal in soal_list:
                nomor = soal.get("nomor")
                if nomor in jawaban["listening"]:
                    jwb_text = jawaban["listening"][nomor]

                    # Untuk listening, jawaban biasanya a/b/c/d
                    # Atau bisa berupa teks
                    if jwb_text in ["①", "a", "1"]:
                        soal["jawaban"] = "a"
                    elif jwb_text in ["②", "b", "2"]:
                        soal["jawaban"] = "b"
                    elif jwb_text in ["③", "c", "3"]:
                        soal["jawaban"] = "c"
                    elif jwb_text in ["④", "d", "4"]:
                        soal["jawaban"] = "d"
                    else:
                        soal["jawaban"] = jwb_text
                    updated += 1

            # Save
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            if updated > 0:
                updated_listening += updated
                print(
                    f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✓ Listening ({updated} soal)"
                )
            else:
                print(
                    f"[{unit_num - 30}/30] Unit {unit_num:02d}: ⚠️  Listening (tidak ada yang diupdate)"
                )

        except Exception as e:
            print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✗ Listening - {e}")
            failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Total jawaban reading diupdate: {updated_reading}")
print(f"Total jawaban listening diupdate: {updated_listening}")
print(f"Unit gagal: {len(failed_units)}")
if failed_units:
    print(f"  Detail: {failed_units}")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_jawaban.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "updated_reading": updated_reading,
            "updated_listening": updated_listening,
            "gagal": failed_units,
            "jawaban_per_unit": {str(k): v for k, v in jawaban_per_unit.items()},
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")

# Verifikasi Unit 31
print("\n=== VERIFIKASI UNIT 31 ===")
reading_path = base_dir / "unit_31" / "reading_data.json"
with open(reading_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Reading (5 soal):")
for soal in data["soal"]:
    print(f"  Soal {soal['nomor']}: jawaban='{soal.get('jawaban', '')}'")

listening_path = base_dir / "unit_31" / "listening_data.json"
with open(listening_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("\nListening (5 soal):")
for soal in data["soal"]:
    print(f"  Soal {soal['nomor']}: jawaban='{soal.get('jawaban', '')}'")

print("\n=== SELESAI ===")
print("Selanjutnya: Upload ke Supabase atau buat frontend!")
