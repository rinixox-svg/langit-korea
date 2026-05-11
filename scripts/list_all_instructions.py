#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List semua instruksi dari seluruh soal di 30 unit (31-60)
Untuk verifikasi apakah instruksi sudah ditempelkan dengan benar
"""

import json
from pathlib import Path

print("=== LIST INSTRUKSI SEMUA SOAL ===\n")

base_dir = Path("../assets/langit-korea-extracted")

laporan = {}

for unit_num in range(31, 61):
    unit_key = f"unit_{unit_num:02d}"
    laporan[unit_key] = {"reading": {}, "listening": {}}

    data_path = base_dir / unit_key / "data.json"

    if not data_path.exists():
        print(f"❌ {unit_key}: data.json tidak ditemukan")
        continue

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ {unit_key}: Error baca JSON - {e}")
        continue

    soal_list = data.get("soal", [])

    print(f"📘 {unit_key} ({data.get('title_id', '')})")

    for soal in soal_list:
        nomor = soal.get("nomor")
        tipe = soal.get("tipe")
        instruksi = soal.get("instruksi", "").strip()

        # Simpan ke laporan
        if tipe == "membaca":
            laporan[unit_key]["reading"][nomor] = instruksi
        else:
            laporan[unit_key]["listening"][nomor] = instruksi

        # Tampilkan
        if instruksi:
            print(f"  ✅ Soal {nomor} ({tipe}): {instruksi}")
        else:
            print(f"  ⚪ Soal {nomor} ({tipe}): (tanpa instruksi)")

    print()

# Cek pola instruksi [X~Y]
print("\n=== VERIFIKASI POLA [X~Y] ===")
pola_ditemukan = 0

for unit_key, content in laporan.items():
    # Cek reading soal
    for nomor, instr in content["reading"].items():
        if instr and "[" in instr and "~" in instr:
            print(f"  🎯 {unit_key} - Soal {nomor} (membaca): {instr}")
            pola_ditemukan += 1

    # Cek listening soal
    for nomor, instr in content["listening"].items():
        if instr and "[" in instr and "~" in instr:
            print(f"  🎯 {unit_key} - Soal {nomor} (mendengarkan): {instr}")
            pola_ditemukan += 1

print(f"\nTotal pola [X~Y] ditemukan: {pola_ditemukan}")

# Simpan laporan ke JSON
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "list_instruksi_semua_soal.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(laporan, f, ensure_ascii=False, indent=2)

print(f"\n💾 Laporan lengkap disimpan ke: {laporan_path}")
print("\n=== SELESAI ===")
