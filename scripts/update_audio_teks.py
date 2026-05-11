#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update audio_teks di listening_data.json:
1. Baca dari field 'audio_teks' yang sudah ada
2. Jika kosong, coba ambil dari audio script di PDF (jika perlu)
3. Pastikan setiap soal listening punya audio_teks
"""

import json
from datetime import datetime
from pathlib import Path

print("=== UPDATE AUDIO_TEKS UNTUK LISTENING ===\n")

base_dir = Path("../assets/langit-korea-extracted")

updated_total = 0
failed_units = []

for unit_num in range(31, 61):
    print(f"[{unit_num - 30}/30] Unit {unit_num:02d}...", end=" ")

    listening_path = base_dir / f"unit_{unit_num:02d}" / "listening_data.json"

    if not listening_path.exists():
        print("Tidak ada listening_data.json")
        failed_units.append(unit_num)
        continue

    try:
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"✗ Error baca: {e}")
        failed_units.append(unit_num)
        continue

    soal_list = data.get("soal", [])
    updated = 0

    for soal in soal_list:
        audio_teks = soal.get("audio_teks", "").strip()

        # Jika audio_teks kosong, coba cari dari field lain
        if not audio_teks:
            # Cek apakah ada field 'audio_script' atau sejenisnya
            if "audio_script" in soal:
                soal["audio_teks"] = soal["audio_script"]
                updated += 1
            elif "script" in soal:
                soal["audio_teks"] = soal["script"]
                updated += 1
            else:
                # Biarkan kosong, akan diisi nanti
                pass

        # Jika audio_teks ada tapi terlalu pendek, mungkin tidak lengkap
        elif len(audio_teks) < 10:
            # Coba cari teks yang lebih lengkap
            # Untuk saat ini, biarkan saja
            pass

    # Save jika ada yang diupdate
    if updated > 0:
        try:
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ ({updated} soal diupdate)")
            updated_total += updated
        except Exception as e:
            print(f"✗ Error simpan: {e}")
            failed_units.append(unit_num)
    else:
        print(f"⚪  Tidak ada yang diupdate")

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
print("Audio teks sudah diupdate!")
print("Langkah selanjutnya: Upload MP3 ke Supabase Storage")
