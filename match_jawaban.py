#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk mengupdate jawaban di data.json tiap unit
Menggunakan referensi dari jawaban_all.json
"""

import json
import re
from pathlib import Path

EXTRACTED_DIR = Path("./langit-korea-extracted")


def normalize_tipe(tipe_str):
    """Normalisasi tipe soal agar sesuai constraint DB"""
    tipe_lower = tipe_str.lower()
    if "baca" in tipe_lower:
        return "membaca"
    elif "dengar" in tipe_lower or "listening" in tipe_lower:
        return "mendengarkan"
    else:
        return "membaca"  # default


def match_jawaban():
    """Match jawaban dari jawaban_all.json ke data.json tiap unit"""

    # Baca jawaban_all.json
    jawaban_file = EXTRACTED_DIR / "jawaban_all.json"
    if not jawaban_file.exists():
        print(f"❌ File {jawaban_file} tidak ditemukan!")
        print("Pastikan file jawaban_all.json ada di folder langit-korea-extracted/")
        return

    print("Membaca jawaban_all.json...")
    with open(jawaban_file, "r", encoding="utf-8") as f:
        jawaban_data = json.load(f)

    print(f"✅ Ditemukan {len(jawaban_data)} entri jawaban")

    # Iterasi tiap unit
    unit_dirs = sorted(
        [
            d
            for d in EXTRACTED_DIR.iterdir()
            if d.is_dir()
            and d.name.startswith("unit_")
            and not d.name.startswith("unit_appendix")
        ]
    )

    print(f"\n📂 {len(unit_dirs)} unit ditemukan")

    total_updated = 0
    total_soal = 0

    for unit_dir in unit_dirs:
        data_path = unit_dir / "data.json"
        if not data_path.exists():
            continue

        # Baca data.json unit
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        unit_num = data.get("unit")
        if not unit_num:
            continue

        soal_list = data.get("soal", [])
        updated_count = 0

        # Update jawaban untuk tiap soal
        for soal in soal_list:
            soal_id = soal.get("id", "")
            tipe = soal.get("tipe", "")
            nomor = soal.get("nomor", 0)

            # Cari jawaban yang cocok di jawaban_all.json
            # Format key di jawaban_all.json bisa bermacam-macam
            possible_keys = [
                f"u{unit_num}_r{nomor}",  # u31_r1
                f"u{unit_num}_l{nomor}",  # u31_l1
                f"{unit_num}_{nomor}",  # 31_1
                f"u{unit_num}m{nomor}",  # u31m1
                f"u{unit_num}l{nomor}",  # u31l1
            ]

            jawaban_found = None
            for key in possible_keys:
                if key in jawaban_data:
                    jawaban_found = jawaban_data[key]
                    break

            # Jika tidak ketemu, cari dengan pattern lain
            if not jawaban_found:
                # Cari berdasarkan unit dan nomor (lebih fleksibel)
                for key, value in jawaban_data.items():
                    if str(unit_num) in key and str(nomor) in key:
                        jawaban_found = value
                        break

            # Update jika ditemukan dan masih "?"
            if jawaban_found:
                # Pastikan jawabannya a/b/c/d
                jawaban_clean = str(jawaban_found).lower().strip()
                if jawaban_clean in ["a", "b", "c", "d"]:
                    if soal.get("jawaban") == "?":
                        soal["jawaban"] = jawaban_clean
                        soal["akses"] = "free"  # Sudah ada jawaban, set free
                        updated_count += 1
                        total_updated += 1

        total_soal += len(soal_list)

        # Simpan kembali data.json jika ada perubahan
        if updated_count > 0:
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(
                f"Unit {unit_num}: ✅ {updated_count}/{len(soal_list)} jawaban diupdate"
            )
        else:
            print(f"Unit {unit_num}: ℹ️ Tidak ada jawaban yang diupdate")

    print("\n" + "=" * 55)
    print("📊 LAPORAN UPDATE JAWABAN")
    print("=" * 55)
    print(f"Total soal diproses: {total_soal}")
    print(f"Total jawaban diupdate: {total_updated}")
    print(f"Jumlah unit diproses: {len(unit_dirs)}")
    print("\n💡 Tips: Jalankan integrate_to_supabase.py lagi untuk upload soal")
    print("=" * 55)


if __name__ == "__main__":
    match_jawaban()
