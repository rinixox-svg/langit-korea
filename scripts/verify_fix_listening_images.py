#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifikasi dan perbaikan gambar untuk soal listening
- Cek jumlah gambar listening per unit
- Update field 'gambar_pilihan' di listening_data.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== VERIFIKASI & PERBAIKI GAMBAR LISTENING ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def get_listening_images(unit_dir):
    """Ambil daftar gambar listening dari folder images"""
    images_dir = unit_dir / "images"
    if not images_dir.exists():
        return []

    # Pattern: u{unit}_h9_soal_listening_{nomor}.{ext}
    pattern = f"u{unit_dir.name.split('_')[1]}_h9_soal_listening_*.jpeg"
    images = list(images_dir.glob("u*_h9_soal_listening_*.jpeg")) + list(
        images_dir.glob("u*_h9_soal_listening_*.png")
    )

    # Sort by nomor
    def extract_num(path):
        match = re.search(r"listening_(\d+)", path.name)
        return int(match.group(1)) if match else 0

    images.sort(key=extract_num)
    return images


def update_listening_with_images(unit_num):
    """Update listening_data.json dengan info gambar"""
    unit_dir = base_dir / f"unit_{unit_num:02d}"
    if not unit_dir.exists():
        return False, "Directory tidak ada"

    # Get images
    image_files = get_listening_images(unit_dir)

    # Load listening data
    listening_path = unit_dir / "listening_data.json"
    if not listening_path.exists():
        return False, "listening_data.json tidak ada"

    try:
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Error baca JSON: {e}"

    soal_list = data.get("soal", [])

    # Update gambar_pilihan for each soal
    updated_count = 0
    for soal in soal_list:
        nomor = soal.get("nomor")

        # Find matching image
        matching_images = [
            img for img in image_files if f"listening_{nomor}" in img.name
        ]

        if matching_images:
            # Assuming 4 images per soal (A, B, C, D)
            img_path = matching_images[0]
            # In real implementation, you'd extract 4 images from PDF
            # For now, just mark that images exist
            soal["gambar_pilihan"] = {
                "a": f"images/{img_path.name}",
                "b": f"images/{img_path.name.replace('_01', '_02')}",
                "c": f"images/{img_path.name.replace('_01', '_03')}",
                "d": f"images/{img_path.name.replace('_01', '_04')}",
            }
            updated_count += 1
        else:
            # No image found, maybe text-based listening
            soal["ada_gambar_pilihan"] = False

    # Save updated data
    try:
        with open(listening_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, f"Updated {updated_count} soal"
    except Exception as e:
        return False, f"Error simpan: {e}"


# Main verification
print("Memulai verifikasi gambar listening...\n")

success_count = 0
failed_units = []
laporan = {}

for unit_num in range(31, 61):
    print(f"[{unit_num - 30}/30] Unit {unit_num:02d}...", end=" ")

    success, message = update_listening_with_images(unit_num)

    if success:
        print(f"✓ ({message})")
        success_count += 1

        # Count images
        unit_dir = base_dir / f"unit_{unit_num:02d}"
        image_files = get_listening_images(unit_dir)
        laporan[unit_num] = {
            "listening_soal": len([s for s in [] if True]),  # Placeholder
            "gambar_count": len(image_files),
        }
    else:
        print(f"✗ ({message})")
        failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success_count}/30")
print(f"Gagal: {len(failed_units)}")
if failed_units:
    print(f"  Unit gagal: {failed_units}")

# Detailed verification for Unit 31
print("\n=== VERIFIKASI DETAIL UNIT 31 ===")
unit_31_dir = base_dir / "unit_31"
listening_path = unit_31_dir / "listening_data.json"

with open(listening_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Jumlah soal listening: {len(data['soal'])}")
print(f"Jumlah gambar di folder images: {len(get_listening_images(unit_31_dir))}")

for soal in data["soal"]:
    nomor = soal["nomor"]
    ada_gambar = soal.get("ada_gambar_pilihan", False)
    gambar_info = soal.get("gambar_pilihan", {})

    print(f"\nSoal {nomor}:")
    print(f"  Ada gambar: {ada_gambar}")
    if gambar_info:
        print(f"  Gambar: {gambar_info}")
    print(f"  Teks soal: {soal['teks_soal'][:50]}...")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_gambar_listening.json"

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
