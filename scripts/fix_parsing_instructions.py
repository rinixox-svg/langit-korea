#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk memperbaiki parsing hal8_soal.txt dan hal9_soal.txt
dengan menangani field 'instruksi' yang muncul di antara soal.

Pola yang ditangani:
1. Instruksi bisa muncul di awal (sebelum soal 1)
2. Instruksi bisa muncul di antara soal (misal: [3~4] ...)
3. Instruksi harus ditempelkan ke soal yang sesuai
"""

import json
import re
from pathlib import Path

print("=== FIX PARSING INSTRUKSI 30 UNIT ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def parse_soal_with_instructions(txt_path, tipe="membaca"):
    """
    Parse file soal (hal8 atau hal9) dengan menangani instruksi
    yang muncul di antara soal.
    """
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading {txt_path}: {e}")
        return []

    lines = text.split("\n")
    soal_list = []
    current_soal = None
    current_number = None
    instruction_buffer = ""
    global_instruction = ""  # Instruksi di awal file

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header like "읽기 READING" or "듣기 LISTENING"
        if re.match(r"^(읽기|듣기)\s+(READING|LISTENING)", line_stripped):
            continue

        # Detect question number (1. 2. 3. 4. 5.)
        match = re.match(r"^(\d+)\.\s*", line_stripped)
        if match:
            # Save previous soal if exists
            if current_soal and current_number:
                # Attach any pending instruction
                if instruction_buffer:
                    current_soal["instruksi"] = instruction_buffer.strip()
                    instruction_buffer = ""
                soal_list.append(current_soal)

            num = int(match.group(1))
            if num > 5:  # Only process 5 questions per page
                break

            current_number = num
            teks = line_stripped[match.end() :].strip()

            current_soal = {
                "nomor": num,
                "tipe": tipe,
                "teks_soal": teks,
                "instruksi": "",  # Will be filled if there's instruction
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
            }
            continue

        if not current_soal:
            # We haven't found first question yet
            # Check if this line is a global instruction
            if re.search(r"\[\d+~\d+\]", line_stripped) or any(
                keyword in line_stripped
                for keyword in ["고르십시오", "알맞은", "들고", "읽고"]
            ):
                if global_instruction:
                    global_instruction += " " + line_stripped
                else:
                    global_instruction = line_stripped
            continue

        # Detect instruction patterns (including [3~4] pattern)
        is_instruction = False
        instr_patterns = [
            r"\[\d+~\d+\].*",  # [3~4] pattern
            r"다음.*고르십시오",
            r"그림을.*고르십시오",
            r"문장.*고르십시오",
            r"가장.*고르십시오",
            r"알맞은.*고르십시오",
            r"내용과.*고르십시오",
            r"들고.*고르십시오",
            r"읽고.*고르십시오",
        ]

        for pat in instr_patterns:
            if re.search(pat, line_stripped):
                is_instruction = True
                break

        # If this is an instruction, buffer it
        if is_instruction:
            if instruction_buffer:
                instruction_buffer += " " + line_stripped
            else:
                instruction_buffer = line_stripped
            continue

        # Detect answer choices ① ② ③ ④
        if "①" in line_stripped or line_stripped.startswith("①"):
            # Parse all choices in this line or multiple lines
            choices = parse_choices(line_stripped)
            if choices.get("a"):
                current_soal["pilihan_a"] = choices["a"]
            if choices.get("b"):
                current_soal["pilihan_b"] = choices["b"]
            if choices.get("c"):
                current_soal["pilihan_c"] = choices["c"]
            if choices.get("d"):
                current_soal["pilihan_d"] = choices["d"]
            continue
        elif line_stripped.startswith("②"):
            current_soal["pilihan_b"] = line_stripped[1:].strip()
            continue
        elif line_stripped.startswith("③"):
            current_soal["pilihan_c"] = line_stripped[1:].strip()
            continue
        elif line_stripped.startswith("④"):
            current_soal["pilihan_d"] = line_stripped[1:].strip()
            continue
        else:
            # Continuation of question text
            if current_soal["teks_soal"]:
                current_soal["teks_soal"] += " " + line_stripped
            else:
                current_soal["teks_soal"] = line_stripped

    # Save last soal
    if current_soal and current_number:
        if instruction_buffer:
            current_soal["instruksi"] = instruction_buffer.strip()
        soal_list.append(current_soal)

    # If we have global instruction and no instruction attached, attach to first soal
    if global_instruction and soal_list:
        if not soal_list[0].get("instruksi"):
            soal_list[0]["instruksi"] = global_instruction

    return soal_list


def parse_choices(line_text):
    """Parse answer choices from a line that may contain ① ② ③ ④"""
    choices = {}
    # Replace Korean circled numbers with markers
    text = line_text
    for sym, key in [("①", "a"), ("②", "b"), ("③", "c"), ("④", "d")]:
        if sym in text:
            parts = text.split(sym)
            if len(parts) > 1:
                choice_text = parts[1].strip()
                # Remove other symbols from choice text
                for other_sym in ["①", "②", "③", "④"]:
                    if other_sym in choice_text:
                        choice_text = choice_text.split(other_sym)[0].strip()
                choices[key] = choice_text
                # Update text for next iteration
                text = sym.join(parts[1:])

    return choices


def update_data_json(unit_num, parsed_reading, parsed_listening):
    """
    Update data.json for a unit with properly parsed soal
    """
    data_path = base_dir / f"unit_{unit_num:02d}" / "data.json"

    if not data_path.exists():
        print(f"  [!] data.json tidak ditemukan untuk unit {unit_num}")
        return False

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [!] Error reading data.json unit {unit_num}: {e}")
        return False

    soal_list = data.get("soal", [])
    updated_count = 0

    # Create lookup dictionaries
    reading_lookup = {s["nomor"]: s for s in parsed_reading if s["tipe"] == "membaca"}
    listening_lookup = {
        s["nomor"]: s for s in parsed_listening if s["tipe"] == "mendengarkan"
    }

    # Update each soal in data.json
    for soal in soal_list:
        nomor = soal.get("nomor")
        tipe = soal.get("tipe")

        if tipe == "membaca" and nomor in reading_lookup:
            parsed = reading_lookup[nomor]

            # Update teks_soal if it's empty or contains choice symbols
            if parsed["teks_soal"]:
                if not soal.get("teks_soal") or "①" in soal.get("teks_soal", ""):
                    soal["teks_soal"] = parsed["teks_soal"]
                    updated_count += 1

            # Update instruksi
            if parsed.get("instruksi"):
                if not soal.get("instruksi") or soal.get("instruksi") == "":
                    soal["instruksi"] = parsed["instruksi"]
                    updated_count += 1

            # Update pilihan
            for key in ["pilihan_a", "pilihan_b", "pilihan_c", "pilihan_d"]:
                if parsed.get(key) and (not soal.get(key) or "①" in soal.get(key, "")):
                    soal[key] = parsed[key]
                    updated_count += 1

        elif tipe == "mendengarkan" and nomor in listening_lookup:
            parsed = listening_lookup[nomor]

            # Update fields similarly
            if parsed["teks_soal"]:
                if not soal.get("teks_soal") or "①" in soal.get("teks_soal", ""):
                    soal["teks_soal"] = parsed["teks_soal"]
                    updated_count += 1

            if parsed.get("instruksi"):
                if not soal.get("instruksi") or soal.get("instruksi") == "":
                    soal["instruksi"] = parsed["instruksi"]
                    updated_count += 1

            for key in ["pilihan_a", "pilihan_b", "pilihan_c", "pilihan_d"]:
                if parsed.get(key) and (not soal.get(key) or "①" in soal.get(key, "")):
                    soal[key] = parsed[key]
                    updated_count += 1

    # Save if updated
    if updated_count > 0:
        try:
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"  [!] Error saving data.json unit {unit_num}: {e}")
            return False

    return False


# Process all 30 units
print("Memulai proses perbaikan parsing...\n")
total_updated = 0
success_units = 0
failed_units = []

for unit in range(31, 61):
    print(f"[{unit - 30}/30] Unit {unit:02d}...", end=" ")

    hal8_path = base_dir / f"unit_{unit:02d}" / "teks" / "hal8_soal.txt"
    hal9_path = base_dir / f"unit_{unit:02d}" / "teks" / "hal9_soal.txt"

    # Parse reading (hal8)
    parsed_reading = []
    if hal8_path.exists():
        parsed_reading = parse_soal_with_instructions(hal8_path, tipe="membaca")
    else:
        print(f"hal8 missing", end=" ")

    # Parse listening (hal9)
    parsed_listening = []
    if hal9_path.exists():
        parsed_listening = parse_soal_with_instructions(hal9_path, tipe="mendengarkan")
    else:
        print(f"hal9 missing", end=" ")

    # Update data.json
    success = update_data_json(unit, parsed_reading, parsed_listening)

    if success:
        print(f"✓ ({len(parsed_reading)} reading, {len(parsed_listening)} listening)")
        total_updated += len(parsed_reading) + len(parsed_listening)
        success_units += 1
    else:
        print(f"✗ (no changes or error)")
        failed_units.append(unit)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Unit berhasil diperbarui: {success_units}/30")
print(f"Unit gagal: {len(failed_units)}")
if failed_units:
    print(f"  Detail: {failed_units}")
print(f"Total soal diproses: {total_updated}")

# Save laporan
laporan = {
    "total_unit_diproses": 30,
    "unit_berhasil": success_units,
    "unit_gagal": failed_units,
    "total_soal_diproses": total_updated,
    "detail_per_unit": {},
}

for unit in range(31, 61):
    hal8_path = base_dir / f"unit_{unit:02d}" / "teks" / "hal8_soal.txt"
    hal9_path = base_dir / f"unit_{unit:02d}" / "teks" / "hal9_soal.txt"

    reading_count = 0
    listening_count = 0

    if hal8_path.exists():
        parsed = parse_soal_with_instructions(hal8_path, "membaca")
        reading_count = len(parsed)

    if hal9_path.exists():
        parsed = parse_soal_with_instructions(hal9_path, "mendengarkan")
        listening_count = len(parsed)

    laporan["detail_per_unit"][f"unit_{unit:02d}"] = {
        "reading": reading_count,
        "listening": listening_count,
    }

laporan_path = Path("./langit-korea-json/laporan_parsing.json")
laporan_path.parent.mkdir(parents=True, exist_ok=True)
with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(laporan, f, ensure_ascii=False, indent=2)

print(f"\nLaporan disimpan ke: {laporan_path}")
print("\n=== SELESAI ===")
