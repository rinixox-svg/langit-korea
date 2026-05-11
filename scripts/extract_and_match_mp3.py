#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk extract MP3 dan match dengan soal listening:
1. Extract MP3 dari ZIP
2. Rename ke format: unit_{unit}_listening_{nomor}.mp3
3. Match dengan soal listening di JSON
"""

import json
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

print("=== EXTRACT & MATCH MP3 UNTUK LISTENING ===\n")

base_dir = Path("../assets/langit-korea-extracted")
zip_path = Path("../assets/EPS-TOPIK_textbook2_listen.zip")
mp3_output_dir = Path("./extracted_mp3")

# Bersihkan direktori output
if mp3_output_dir.exists():
    shutil.rmtree(mp3_output_dir)
mp3_output_dir.mkdir(parents=True, exist_ok=True)

print("=== EKSTRAKSI MP3 ===")

try:
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Filter file MP3
        mp3_files = [f for f in zip_ref.namelist() if f.endswith(".mp3")]
        print(f"✓ Ditemukan {len(mp3_files)} file MP3")

        # Extract semua MP3
        for mp3_file in mp3_files:
            zip_ref.extract(mp3_file, mp3_output_dir)

        print(f"✓ MP3 diekstrak ke: {mp3_output_dir}")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Sekarang kita perlu mapping MP3 ke unit
# Pola: Biasanya MP3 diurutkan: 5 soal per unit, mulai dari unit 31
# Total: 30 unit × 5 soal = 150 MP3

print("\n=== MAPPING MP3 KE UNIT ===")

# Kumpulkan semua file MP3 yang diekstrak
all_mp3 = list(mp3_output_dir.glob("**/*.mp3"))
all_mp3_sorted = sorted(all_mp3)  # Sort by nama

print(f"✓ Total MP3: {len(all_mp3_sorted)}")

# Mapping: index MP3 -> (unit, nomor)
mp3_mapping = {}
current_unit = 31
current_soal = 1

for idx, mp3_path in enumerate(all_mp3_sorted):
    # Setiap 5 MP3 = 1 unit
    unit_num = 31 + (idx // 5)
    soal_num = (idx % 5) + 1

    # Rename file ke format yang jelas
    new_name = f"unit_{unit_num:02d}_listening_{soal_num}.mp3"
    new_path = mp3_output_dir / new_name

    # Copy (jangan move, biarkan originalnya)
    shutil.copy2(mp3_path, new_path)

    mp3_mapping[(unit_num, soal_num)] = new_path
    print(f"  MP3 {idx + 1}: Unit {unit_num:02d} Soal {soal_num} -> {new_name}")

print(f"\n✓ Mapping selesai: {len(mp3_mapping)} MP3")

# Sekarang update listening_data.json dengan audio_url
print("\n=== UPDATE LISTENING DATA DENGAN AUDIO URL ===")

updated_total = 0
failed_units = []

for unit_num in range(31, 61):
    listening_path = base_dir / f"unit_{unit_num:02d}" / "listening_data.json"

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

    for soal in soal_list:
        nomor = soal.get("nomor")
        mp3_key = (unit_num, nomor)

        if mp3_key in mp3_mapping:
            mp3_path = mp3_mapping[mp3_key]
            # Untuk saat ini, simpan path relatif
            # Nanti saat upload ke Supabase Storage, kita ganti dengan public URL
            soal["audio_file"] = str(mp3_path)
            updated += 1

    # Save
    if updated > 0:
        try:
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✓ ({updated} soal)")
            updated_total += updated
        except Exception as e:
            print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ✗ Error simpan - {e}")
            failed_units.append(unit_num)
    else:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}: ⚠️  Tidak ada MP3 yang cocok")

print(f"\n=== LAPORAN AKHIR ===")
print(f"Total listening soal diupdate dengan audio: {updated_total}")
print(f"Unit gagal: {len(failed_units)}")
if failed_units:
    print(f"  Detail: {failed_units}")

# Verifikasi Unit 31
print("\n=== VERIFIKASI UNIT 31 ===")
listening_path = base_dir / "unit_31" / "listening_data.json"
with open(listening_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Listening (5 soal):")
for soal in data["soal"]:
    nomor = soal["nomor"]
    audio_file = soal.get("audio_file", "")
    print(f"  Soal {nomor}: audio='{audio_file}'")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_mp3_mapping.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "updated": updated_total,
            "gagal": failed_units,
            "mapping": {f"{k[0]}_{k[1]}": str(v) for k, v in mp3_mapping.items()},
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
print("MP3 sudah diekstrak dan dimapping ke listening_data.json!")
print(
    "Langkah selanjutnya: Upload MP3 ke Supabase Storage, kemudian update audio_url di JSON."
)
