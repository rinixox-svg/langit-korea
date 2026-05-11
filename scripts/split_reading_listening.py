#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk memisahkan soal reading dan listening ke file terpisah
Setiap unit akan memiliki:
- reading_data.json (soal membaca)
- listening_data.json (soal mendengarkan)
"""

import json
from pathlib import Path

print("=== MEMISAHKAN SOAL READING & LISTENING ===\n")

base_dir = Path("../assets/langit-korea-extracted")

success_count = 0
failed_units = []

for unit_num in range(31, 61):
    unit_key = f"unit_{unit_num:02d}"
    unit_dir = base_dir / unit_key
    data_path = unit_dir / "data.json"

    if not data_path.exists():
        print(f"[{unit_num - 30}/30] {unit_key}: data.json tidak ditemukan")
        failed_units.append(unit_num)
        continue

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[{unit_num - 30}/30] {unit_key}: Error baca JSON - {e}")
        failed_units.append(unit_num)
        continue

    # Ambil metadata unit
    unit_meta = {
        "unit": data.get("unit"),
        "title_ko": data.get("title_ko", ""),
        "title_id": data.get("title_id", ""),
        "file": data.get("file", ""),
        "total_halaman": data.get("total_halaman", 10),
    }

    # Pisahkan soal
    soal_list = data.get("soal", [])
    reading_soal = [s for s in soal_list if s.get("tipe") == "membaca"]
    listening_soal = [s for s in soal_list if s.get("tipe") == "mendengarkan"]

    # Simpan reading_data.json
    reading_data = {**unit_meta, "soal": reading_soal}
    reading_path = unit_dir / "reading_data.json"
    try:
        with open(reading_path, "w", encoding="utf-8") as f:
            json.dump(reading_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[{unit_num - 30}/30] {unit_key}: Error simpan reading - {e}")
        failed_units.append(unit_num)
        continue

    # Simpan listening_data.json
    listening_data = {**unit_meta, "soal": listening_soal}
    listening_path = unit_dir / "listening_data.json"
    try:
        with open(listening_path, "w", encoding="utf-8") as f:
            json.dump(listening_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[{unit_num - 30}/30] {unit_key}: Error simpan listening - {e}")
        failed_units.append(unit_num)
        continue

    print(
        f"[{unit_num - 30}/30] {unit_key}: ✓ (R:{len(reading_soal)}, L:{len(listening_soal)})"
    )
    success_count += 1

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success_count}/30")
print(f"Gagal: {len(failed_units)}")
if failed_units:
    print(f"Unit gagal: {failed_units}")

print("\n=== SELESAI ===")
