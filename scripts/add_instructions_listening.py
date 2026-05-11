#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buat instruksi untuk soal listening berdasarkan pola umum:
1. Soal 1: "다음을 듣고 들은 내용과 관계있는 그림을 고르십시오."
2. Soal 2: "다음을 듣고 물음에 알맞은 대답을 고르십시오."
3. Soal 3: "두 사람은 무엇에 대해 말하고 있습니까?"
4. Soal 4: "다음을 듣고 이어지는 말로 가장 알맞은 것을 고르십시오."
5. Soal 5: "남자가 이어서 할 행동은 무엇입니까?"
"""

import json
from datetime import datetime
from pathlib import Path

print("=== BUAT INSTRUKSI LISTENING ===\n")

base_dir = Path("../assets/langit-korea-extracted")

# Pola instruksi umum untuk listening
instruksi_pola = {
    1: "다음을 듣고 들은 내용과 관계있는 그림을 고르십시오.",
    2: "다음을 듣고 물음에 알맞은 대답을 고르십시오.",
    3: "두 사람은 무엇에 대해 말하고 있습니까?",
    4: "다음을 듣고 이어지는 말로 가장 알맞은 것을 고르십시오.",
    5: "남자가 이어서 할 행동은 무엇입니까?",
}

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
        nomor = soal.get("nomor")

        # Jika instruksi kosong, isi dengan pola umum
        if not soal.get("instruksi"):
            if nomor in instruksi_pola:
                soal["instruksi"] = instruksi_pola[nomor]
                updated += 1

    # Save jika ada yang diupdate
    if updated > 0:
        try:
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ ({updated} soal)")
            updated_total += updated
        except Exception as e:
            print(f"✗ Error simpan: {e}")
            failed_units.append(unit_num)
    else:
        print("⚪  Tidak ada yang diupdate")

print(f"\n=== LAPORAN AKHIR ===")
print(f"Total instruksi ditambahkan: {updated_total}")
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
    instruksi = soal.get("instruksi", "")
    print(f"  Soal {nomor}: instruksi='{instruksi}'")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_instructions_listening.json"

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
print("Instruksi listening sudah ditambahkan!")
print("Langkah selanjutnya: Setup Supabase dan upload data")
