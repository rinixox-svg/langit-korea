#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifikasi detail: Menampilkan teks soal lengkap + instruksi
fokus pada soal yang memiliki instruksi pola [X~Y]
"""

import json
from pathlib import Path

print("=== VERIFIKASI DETAIL INSTRUKSI [X~Y] ===\n")

base_dir = Path("../assets/langit-korea-extracted")

# Cek beberapa unit yang biasanya punya pola [X~Y]
units_to_check = [31, 32, 34, 35, 39, 43, 45, 49, 51, 53]

for unit_num in units_to_check:
    unit_key = f"unit_{unit_num:02d}"
    data_path = base_dir / unit_key / "data.json"

    if not data_path.exists():
        continue

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📘 {unit_key} - {data.get('title_id', '')}")
    print(f"{'=' * 60}")

    soal_list = data.get("soal", [])

    # Filter hanya soal membaca
    reading_soal = [s for s in soal_list if s.get("tipe") == "membaca"]

    for soal in reading_soal:
        nomor = soal.get("nomor")
        teks = soal.get("teks_soal", "")
        instruksi = soal.get("instruksi", "").strip()

        print(f"\n[Soal {nomor}]")
        print(f"  Teks Soal: {teks[:80]}{'...' if len(teks) > 80 else ''}")

        if instruksi:
            print(f"  ✅ Instruksi: {instruksi}")
        else:
            # Cek apakah teks soal mengandung instruksi
            if any(kw in teks for kw in ["다음", "고르십시오", "읽고", "들고"]):
                print(f"  ⚠️  Teks soal mengandung instruksi (mungkin belum dipisah)")
            else:
                print(f"  ⚪ (Tanpa instruksi terpisah)")

        # Tampilkan pilihan (first 30 chars each)
        pilihan = []
        for key in ["pilihan_a", "pilihan_b", "pilihan_c", "pilihan_d"]:
            val = soal.get(key, "")
            if val:
                pilihan.append(f"{key[-1].upper()}:{val[:20]}")
        print(f"  Pilihan: {' | '.join(pilihan)}")

    print(f"\n{'=' * 60}\n")

# Cek langsung file hal8_soal.txt untuk melihat format asli [X~Y]
print("\n=== CEK FORMAT ASLI [X~Y] DI FILE TXT ===\n")

for unit_num in [31, 34, 39]:
    txt_path = base_dir / f"unit_{unit_num:02d}" / "teks" / "hal8_soal.txt"

    if not txt_path.exists():
        continue

    print(f"📄 Unit {unit_num:02d} - hal8_soal.txt:")

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Cari baris yang mengandung [X~Y]
    for i, line in enumerate(lines):
        if "[" in line and "~" in line:
            print(f"  Baris {i + 1}: {line.strip()}")

    print()

print("=== SELESAI ===")
