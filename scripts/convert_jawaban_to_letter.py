#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konversi jawaban dari teks ke a/b/c/d
Untuk reading: cari di pilihan_a/b/c/d
Untuk listening: biasanya a/b/c/d (1/2/3/4)
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== KONVERSI JAWABAN KE A/B/C/D ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def convert_jawaban_to_letter(soal_list, tipe="membaca"):
    """Konversi field jawaban ke a/b/c/d"""
    converted = 0
    failed = 0

    for soal in soal_list:
        jawaban_text = soal.get("jawaban", "").strip()
        if not jawaban_text:
            continue

        # Untuk reading: cari di pilihan
        if tipe == "membaca":
            # Cek apakah jawaban_text ada di pilihan_a
            if jawaban_text in soal.get("pilihan_a", ""):
                soal["jawaban"] = "a"
                converted += 1
            elif jawaban_text in soal.get("pilihan_b", ""):
                soal["jawaban"] = "b"
                converted += 1
            elif jawaban_text in soal.get("pilihan_c", ""):
                soal["jawaban"] = "c"
                converted += 1
            elif jawaban_text in soal.get("pilihan_d", ""):
                soal["jawaban"] = "d"
                converted += 1
            else:
                # Mungkin formatnya sudah a/b/c/d
                if jawaban_text.lower() in ["a", "b", "c", "d", "①", "②", "③", "④"]:
                    # Normalize
                    mapping = {
                        "①": "a",
                        "②": "b",
                        "③": "c",
                        "④": "d",
                        "1": "a",
                        "2": "b",
                        "3": "c",
                        "4": "d",
                    }
                    soal["jawaban"] = mapping.get(jawaban_text, jawaban_text.lower())
                    converted += 1
                else:
                    failed += 1
        else:  # listening
            # Untuk listening, jawaban biasanya berupa teks dialog
            # Kita asumsikan jawaban listening adalah a/b/c/d
            # Atau bisa dari pola: 1., 2., 3., 4. atau ①, ②, ③, ④
            if re.match(r"^[①②③④]$", jawaban_text):
                mapping = {"①": "a", "②": "b", "③": "c", "④": "d"}
                soal["jawaban"] = mapping[jawaban_text]
                converted += 1
            elif re.match(r"^[1-4]$", jawaban_text):
                mapping = {"1": "a", "2": "b", "3": "c", "4": "d"}
                soal["jawaban"] = mapping[jawaban_text]
                converted += 1
            elif jawaban_text.lower() in ["a", "b", "c", "d"]:
                soal["jawaban"] = jawaban_text.lower()
                converted += 1
            else:
                # Biarkan sebagai teks (mungkin memang begitu)
                failed += 1

    return converted, failed


# Proses semua unit
print("Memulai konversi...\n")

total_converted = 0
total_failed = 0
laporan = {}

for unit_num in range(31, 61):
    unit_dir = base_dir / f"unit_{unit_num:02d}"
    unit_key = f"unit_{unit_num:02d}"
    unit_laporan = {"reading": {}, "listening": {}}

    # Process reading
    reading_path = unit_dir / "reading_data.json"
    if reading_path.exists():
        try:
            with open(reading_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            reading_soal = data.get("soal", [])
            converted, failed = convert_jawaban_to_letter(reading_soal, "membaca")
            total_converted += converted
            total_failed += failed

            # Save
            with open(reading_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            unit_laporan["reading"] = {"converted": converted, "failed": failed}
        except Exception as e:
            print(f"[{unit_num - 30}/30] {unit_key} Reading ✗: {e}")

    # Process listening
    listening_path = unit_dir / "listening_data.json"
    if listening_path.exists():
        try:
            with open(listening_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            listening_soal = data.get("soal", [])
            converted, failed = convert_jawaban_to_letter(
                listening_soal, "mendengarkan"
            )
            total_converted += converted
            total_failed += failed

            # Save
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            unit_laporan["listening"] = {"converted": converted, "failed": failed}
            print(f"[{unit_num - 30}/30] {unit_key}: R✓ L✓")
        except Exception as e:
            print(f"[{unit_num - 30}/30] {unit_key} Listening ✗: {e}")

    laporan[unit_key] = unit_laporan

print(f"\n=== LAPORAN AKHIR ===")
print(f"Total konversi berhasil: {total_converted}")
print(f"Total gagal: {total_failed}")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_konversi_jawaban.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "total_converted": total_converted,
            "total_failed": total_failed,
            "detail": laporan,
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
print("Semua jawaban sudah dalam format a/b/c/d!")
print("Langkah selanjutnya: Upload ke Supabase!")
