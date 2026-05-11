#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mengisi audio_teks di listening_data.json:
1. Baca hal9_soal.txt
2. Ambil bagian "듣기지문" (audio script)
3. Masukkan ke field 'audio_teks' di listening_data.json
"""

import json
from datetime import datetime
from pathlib import Path

print("=== MENGISI AUDIO_TEKS DI LISTENING DATA ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def extract_audio_script(txt_path):
    """Ambil bagian 듣기지문 dari hal9_soal.txt"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return ""

    # Cari bagian "듣기지문"
    if "듣기지문" in text:
        parts = text.split("듣기지문")
        if len(parts) > 1:
            # Ambil teks setelah "듣기지문"
            script = parts[1].strip()
            # Hapus nomor halaman di akhir (jika ada)
            lines = script.split("\n")
            # Ambil hanya bagian script (sebelum nomor halaman)
            script_lines = []
            for line in lines:
                # Skip baris kosong
                if not line.strip():
                    continue
                # Stop jika ketemu angka (nomo halaman)
                if line.strip().isdigit():
                    break
                script_lines.append(line)
            return "\n".join(script_lines).strip()
    return ""


# Proses semua unit
updated_total = 0
failed_units = []

for unit_num in range(31, 61):
    print(f"[{unit_num - 30}/30] Unit {unit_num:02d}...", end=" ")

    unit_dir = base_dir / f"unit_{unit_num:02d}"
    if not unit_dir.exists():
        print("Tidak ada")
        failed_units.append(unit_num)
        continue

    # Baca hal9_soal.txt
    hal9_path = unit_dir / "teks" / "hal9_soal.txt"
    if not hal9_path.exists():
        print("hal9 tidak ada")
        failed_units.append(unit_num)
        continue

    # Extract audio script
    audio_script = extract_audio_script(hal9_path)

    if not audio_script:
        print("⚠️  Audio script tidak ditemukan")
        continue

    # Update listening_data.json
    listening_path = unit_dir / "listening_data.json"
    if not listening_path.exists():
        print("listening_data.json tidak ada")
        failed_units.append(unit_num)
        continue

    try:
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"✗ Error: {e}")
        failed_units.append(unit_num)
        continue

    soal_list = data.get("soal", [])
    updated = 0

    # Isi audio_teks untuk semua soal listening di unit ini
    for soal in soal_list:
        if not soal.get("audio_teks"):
            soal["audio_teks"] = audio_script
            updated += 1

    # Save
    try:
        with open(listening_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ ({updated} soal)")
        updated_total += updated
    except Exception as e:
        print(f"✗ Error simpan: {e}")
        failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Total audio_teks diupdate: {updated_total}")
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
    audio_teks = soal.get("audio_teks", "")
    print(f"  Soal {nomor}: audio_teks='{audio_teks[:50]}...' (len={len(audio_teks)})")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_audio_teks.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "updated": updated_total,
            "gagal": failed_units,
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
print("Audio teks sudah terisi di listening_data.json!")
print("Langkah selanjutnya: Upload MP3 ke Supabase Storage")
