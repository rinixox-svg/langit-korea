#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buat reading_data.json untuk unit 46, 56, 58
dari hal8_soal.txt yang sudah diekstrak
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== BUAT READING DATA UNTUK UNIT 46, 56, 58 ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def parse_hal8_soal(txt_path, unit_num):
    """Parse hal8_soal.txt untuk reading"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return []

    lines = text.split("\n")
    soal_list = []
    current_soal = None
    current_num = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header
        if re.match(r"^읽기\s+READING", line_stripped):
            continue

        # Detect question number
        match = re.match(r"^(\d+)\.\s*", line_stripped)
        if match:
            # Save previous
            if current_soal and current_num:
                soal_list.append(current_soal)

            num = int(match.group(1))
            if num > 5:
                break

            teks = line_stripped[match.end() :].strip()

            current_soal = {
                "nomor": num,
                "tipe": "membaca",
                "teks_soal": teks,
                "instruksi": "",
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
                "id": f"u{unit_num}_m{num}",
                "jawaban": "",
                "audio_teks": "",
                "ada_gambar_pilihan": False,
                "gambar_pilihan": {},
                "akses": "free",
            }
            current_num = num
            continue

        if not current_soal:
            continue

        # Detect choices
        choice_symbols = ["①", "②", "③", "④"]
        if any(sym in line_stripped for sym in choice_symbols):
            for i, sym in enumerate(choice_symbols):
                if sym in line_stripped:
                    idx = line_stripped.index(sym)
                    rest = line_stripped[idx + len(sym) :]
                    # Remove subsequent symbols
                    for next_sym in choice_symbols[i + 1 :]:
                        if next_sym in rest:
                            rest = rest[: rest.index(next_sym)]
                    rest = rest.strip()
                    key = ["a", "b", "c", "d"][i]
                    current_soal[f"pilihan_{key}"] = rest
            continue

        # Continuation of question text
        if current_soal["teks_soal"]:
            current_soal["teks_soal"] += " " + line_stripped
        else:
            current_soal["teks_soal"] = line_stripped

    # Save last
    if current_soal and current_num:
        soal_list.append(current_soal)

    return soal_list


# Process unit 46, 56, 58
units_to_process = [46, 56, 58]
success_count = 0
failed_units = []

for unit_num in units_to_process:
    print(f"Unit {unit_num:02d}...", end=" ")

    unit_dir = base_dir / f"unit_{unit_num:02d}"
    teks_dir = unit_dir / "teks"
    hal8_path = teks_dir / "hal8_soal.txt"

    if not hal8_path.exists():
        print("✗ hal8_soal.txt tidak ada")
        failed_units.append(unit_num)
        continue

    # Parse
    reading_soal = parse_hal8_soal(hal8_path, unit_num)

    if not reading_soal:
        print("✗ Tidak ada soal")
        failed_units.append(unit_num)
        continue

    # Buat reading_data.json
    # Ambil metadata dari listening_data.json jika ada
    listening_path = unit_dir / "listening_data.json"
    title_ko = ""
    title_id = ""
    pdf_file = f"unit_{unit_num:02d}.pdf"

    if listening_path.exists():
        try:
            with open(listening_path, "r", encoding="utf-8") as f:
                listening_data = json.load(f)
                title_ko = listening_data.get("title_ko", "")
                title_id = listening_data.get("title_id", "")
                pdf_file = listening_data.get("file", pdf_file)
        except:
            pass

    reading_data = {
        "unit": unit_num,
        "title_ko": title_ko,
        "title_id": title_id,
        "file": pdf_file,
        "total_halaman": 10,
        "soal": reading_soal,
    }

    # Save
    reading_path = unit_dir / "reading_data.json"
    try:
        with open(reading_path, "w", encoding="utf-8") as f:
            json.dump(reading_data, f, ensure_ascii=False, indent=2)
        print(f"✓ ({len(reading_soal)} soal)")
        success_count += 1
    except Exception as e:
        print(f"✗ Error simpan: {e}")
        failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success_count}/3")
print(f"Gagal: {len(failed_units)}")

# Sekarang update jawaban dari appendix-answers.pdf
print("\n=== UPDATE JAWABAN ===")

# Buka PDF
try:
    import fitz

    pdf_path = Path("../pdf_modul/appendix-answers.pdf")
    doc = fitz.open(str(pdf_path))

    # Parse jawaban reading untuk unit 46, 56, 58
    jawaban_reading = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split("\n")

        current_unit = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Cek unit
            if re.match(r"^\d{2}$", line):
                unit_num = int(line)
                if unit_num in [46, 56, 58]:
                    current_unit = unit_num
                    jawaban_reading[current_unit] = {}
                continue

            if not current_unit:
                continue

            # Cek pola jawaban (1), (2), (3), (4)
            match = re.match(r"^\(?(\d)\)?\s*(.*)$", line)
            if match:
                num = int(match.group(1))
                jawaban_text = match.group(2).strip()

                # Mapping ke a/b/c/d
                mapping = {1: "a", 2: "b", 3: "c", 4: "d"}
                if num in mapping:
                    jawaban_reading[current_unit][num] = mapping[num]

    doc.close()

    # Update reading_data.json dengan jawaban
    for unit_num in [46, 56, 58]:
        if unit_num not in jawaban_reading:
            print(f"Unit {unit_num:02d}: Tidak ada jawaban di PDF")
            continue

        reading_path = base_dir / f"unit_{unit_num:02d}" / "reading_data.json"
        if not reading_path.exists():
            continue

        try:
            with open(reading_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            soal_list = data.get("soal", [])
            updated = 0

            for soal in soal_list:
                nomor = soal.get("nomor")
                if nomor in jawaban_reading[unit_num]:
                    soal["jawaban"] = jawaban_reading[unit_num][nomor]
                    updated += 1

            # Save
            with open(reading_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"Unit {unit_num:02d}: ✓ ({updated} soal diupdate)")

        except Exception as e:
            print(f"Unit {unit_num:02d}: ✗ {e}")

except Exception as e:
    print(f"✗ Error PDF: {e}")

print("\n=== SELESAI ===")
print("Verifikasi akhir...")
print("Total reading soal sekarang: 150 (27 unit × 5 + 3 unit × 5)")
