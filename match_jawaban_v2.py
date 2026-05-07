#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk mengupdate jawaban di data.json tiap unit
Menggunakan referensi dari jawaban_all.json
"""

import json
from pathlib import Path

EXTRACTED_DIR = Path("./langit-korea-extracted")


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

    print(f"✅ Ditemukan {len(jawaban_data)} unit jawaban")

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

        unit_num = str(data.get("unit", ""))
        if not unit_num:
            continue

        # Cari jawaban untuk unit ini
        unit_jawaban = jawaban_data.get(unit_num, {})
        if not unit_jawaban:
            print(f"Unit {unit_num}: ℹ️ Tidak ada jawaban di jawaban_all.json")
            continue

        soal_list = data.get("soal", [])
        updated_count = 0

        # Update jawaban untuk tiap soal
        for soal in soal_list:
            soal_id = soal.get("id", "")
            tipe = soal.get("tipe", "")
            nomor = soal.get("nomor", 0)

            # Tentukan kategori (membaca atau mendengarkan)
            if "baca" in tipe.lower():
                kategori = "membaca"
            elif "dengar" in tipe.lower() or "listening" in tipe.lower():
                kategori = "mendengarkan"
            else:
                kategori = "membaca"  # default

            # Cari jawaban berdasarkan kategori dan nomor
            kategori_jawaban = unit_jawaban.get(kategori, {})
            jawaban = kategori_jawaban.get(str(nomor), "")

            # Jika tidak ketemu, coba cari langsung
            if not jawaban:
                jawaban = unit_jawaban.get(str(nomor), "")

            # Update jika ditemukan dan masih "?"
            if jawaban and soal.get("jawaban") == "?":
                # Pastikan jawabannya a/b/c/d
                jawaban_clean = str(jawaban).lower().strip()
                if jawaban_clean in ["a", "b", "c", "d"]:
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
