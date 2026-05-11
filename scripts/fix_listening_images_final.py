#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk mengaitkan gambar listening yang sebenarnya
- Cek pola penamaan gambar di folder images
- Update gambar_pilihan dengan benar
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== MENGAIKAN GAMBAR LISTENING ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def analyze_listening_images(unit_num):
    """Analisis gambar listening di folder images"""
    unit_dir = base_dir / f"unit_{unit_num:02d}"
    images_dir = unit_dir / "images"

    if not images_dir.exists():
        return []

    # Cari semua gambar listening
    # Pola: u{unit}_h9_soal_listening_{nomor}.{ext}
    # Atau: u{unit}_h9_soal_listening_{nomor}_{abcd}.{ext}

    listening_images = []

    # Cek pola 1: u31_h9_soal_listening_01.jpeg (1 gambar per soal)
    for ext in ["*.jpeg", "*.jpg", "*.png"]:
        listening_images.extend(
            images_dir.glob(f"u{unit_num:02d}_h9_soal_listening_*{ext}")
        )

    # Sort berdasarkan nomor
    def extract_num(img_path):
        # Coba ekstrak nomor dari nama file
        match = re.search(r"listening_(\d+)", img_path.name)
        if match:
            return int(match.group(1))
        return 0

    listening_images.sort(key=extract_num)
    return listening_images


def update_listening_with_real_images(unit_num):
    """Update listening_data.json dengan gambar yang ada"""
    unit_dir = base_dir / f"unit_{unit_num:02d}"
    listening_path = unit_dir / "listening_data.json"

    if not listening_path.exists():
        return False, "listening_data.json tidak ada"

    # Ambil daftar gambar
    images = analyze_listening_images(unit_num)

    if not images:
        return False, "Tidak ada gambar listening"

    # Load listening data
    try:
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Error baca JSON: {e}"

    soal_list = data.get("soal", [])

    # Update setiap soal dengan gambar yang sesuai
    updated = 0
    for soal in soal_list:
        nomor = soal.get("nomor")

        # Cari gambar untuk soal ini
        matching = [
            img
            for img in images
            if f"listening_{nomor:02d}" in img.name
            or (
                f"listening_{nomor}" in img.name
                and len(img.name) - img.name.find("listening_") <= 5
            )
        ]

        if matching:
            # Asumsi: ada 4 gambar per soal (A, B, C, D)
            # Cari gambar dengan akhiran _a, _b, _c, _d atau 1,2,3,4
            img_dict = {}

            for img in matching[:4]:  # Ambil max 4 gambar
                img_name = img.name

                # Tentukan opsi (a/b/c/d)
                if "_a." in img_name or "1." in img_name:
                    img_dict["a"] = f"images/{img_name}"
                elif "_b." in img_name or "2." in img_name:
                    img_dict["b"] = f"images/{img_name}"
                elif "_c." in img_name or "3." in img_name:
                    img_dict["c"] = f"images/{img_name}"
                elif "_d." in img_name or "4." in img_name:
                    img_dict["d"] = f"images/{img_name}"
                else:
                    # Jika tidak ada suffix, asumsikan urutan
                    if "a" not in img_dict:
                        img_dict["a"] = f"images/{img_name}"
                    elif "b" not in img_dict:
                        img_dict["b"] = f"images/{img_name}"
                    elif "c" not in img_dict:
                        img_dict["c"] = f"images/{img_name}"
                    elif "d" not in img_dict:
                        img_dict["d"] = f"images/{img_name}"

            # Jika hanya ada 1 gambar, gunakan untuk semua opsi (atau tandai tidak ada gambar)
            if len(img_dict) == 1:
                first_key = list(img_dict.keys())[0]
                first_val = img_dict[first_key]
                soal["gambar_pilihan"] = {
                    "a": first_val.replace("01", "01").replace("1.", "a."),
                    "b": first_val.replace("01", "02").replace("1.", "b."),
                    "c": first_val.replace("01", "03").replace("1.", "c."),
                    "d": first_val.replace("01", "04").replace("1.", "d."),
                }
            else:
                soal["gambar_pilihan"] = img_dict

            soal["ada_gambar_pilihan"] = True
            updated += 1
        else:
            # Tidak ada gambar untuk soal ini
            soal["ada_gambar_pilihan"] = False
            soal["gambar_pilihan"] = {}

    # Save
    try:
        with open(listening_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, f"Updated {updated} soal dengan gambar"
    except Exception as e:
        return False, f"Error simpan: {e}"


# Main execution
success_count = 0
failed_units = []
laporan = {}

for unit_num in range(31, 61):
    print(f"[{unit_num - 30}/30] Unit {unit_num:02d}...", end=" ")

    success, message = update_listening_with_real_images(unit_num)

    if success:
        print(f"✓ ({message})")
        success_count += 1

        # Hitung gambar
        images = analyze_listening_images(unit_num)
        laporan[unit_num] = {"gambar_count": len(images), "message": message}
    else:
        print(f"✗ ({message})")
        failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success_count}/30")
print(f"Gagal: {len(failed_units)}")
if failed_units:
    print(f"Unit gagal: {failed_units}")

# Verifikasi Unit 31
print("\n=== VERIFIKASI UNIT 31 ===")
unit_31_path = base_dir / "unit_31" / "listening_data.json"
with open(unit_31_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for soal in data["soal"][:4]:  # Cek 4 soal pertama
    print(f"\nSoal {soal['nomor']}:")
    print(f"  Ada gambar: {soal.get('ada_gambar_pilihan')}")
    gambar = soal.get("gambar_pilihan", {})
    if gambar:
        for key, val in gambar.items():
            print(f"    {key}: {val}")
    else:
        print(f"    (Tidak ada gambar)")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_gambar_final.json"

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
