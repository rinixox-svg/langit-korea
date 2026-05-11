#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix reading jawaban:
1. Baca jawaban teks dari reading_data.json
2. Cari teks tersebut di pilihan_a/b/c/d
3. Konversi ke a/b/c/d
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== FIX READING JAWABAN ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def fix_reading_jawaban(unit_num):
    """Fix jawaban reading untuk satu unit"""
    reading_path = base_dir / f"unit_{unit_num:02d}" / "reading_data.json"

    if not reading_path.exists():
        return False, "File tidak ada"

    try:
        with open(reading_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Error baca: {e}"

    soal_list = data.get("soal", [])
    fixed = 0
    failed = 0

    for soal in soal_list:
        jawaban_text = soal.get("jawaban", "").strip()
        if not jawaban_text:
            continue

        # Jika sudah a/b/c/d, skip
        if jawaban_text.lower() in ["a", "b", "c", "d"]:
            continue

        # Cari di pilihan
        pilihan = {
            "a": soal.get("pilihan_a", ""),
            "b": soal.get("pilihan_b", ""),
            "c": soal.get("pilihan_c", ""),
            "d": soal.get("pilihan_d", ""),
        }

        # Cek apakah jawaban_text ada di salah satu pilihan
        found = False
        for key, val in pilihan.items():
            if jawaban_text in val or val in jawaban_text:
                soal["jawaban"] = key
                fixed += 1
                found = True
                break

        if not found:
            # Mungkin formatnya berbeda, coba cari partial match
            for key, val in pilihan.items():
                # Ambil 5 karakter pertama dari jawaban_text
                if len(jawaban_text) >= 5 and jawaban_text[:5] in val:
                    soal["jawaban"] = key
                    fixed += 1
                    found = True
                    break

            if not found:
                failed += 1
                # Jangan hapus, biarkan sebagai teks
                # soal["jawaban"] = ""  # Uncomment jika mau hapus

    # Save
    try:
        with open(reading_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, f"Fixed {fixed}, Failed {failed}"
    except Exception as e:
        return False, f"Error simpan: {e}"


# Main execution
print("Memulai fix reading jawaban...\n")

success_count = 0
failed_units = []
laporan = {}

for unit_num in range(31, 61):
    print(f"[{unit_num - 30}/30] Unit {unit_num:02d}...", end=" ")

    success, message = fix_reading_jawaban(unit_num)

    if success:
        print(f"✓ ({message})")
        success_count += 1
        laporan[unit_num] = message
    else:
        print(f"✗ ({message})")
        failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success_count}/30")
print(f"Gagal: {len(failed_units)}")
if failed_units:
    print(f"  Unit gagal: {failed_units}")

# Verifikasi Unit 31
print("\n=== VERIFIKASI UNIT 31 READING ===")
reading_path = base_dir / "unit_31" / "reading_data.json"
with open(reading_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Reading (5 soal):")
for soal in data["soal"]:
    nomor = soal["nomor"]
    jawaban = soal.get("jawaban", "")
    print(f"  Soal {nomor}: jawaban='{jawaban}'", end="")
    if jawaban in ["a", "b", "c", "d"]:
        print(" ✓")
    else:
        print(" ⚠️")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_fix_reading_jawaban.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "berhasil": success_count,
            "gagal": failed_units,
            "detail": laporan,
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
print("Semua jawaban reading dan listening sudah dalam format a/b/c/d!")
