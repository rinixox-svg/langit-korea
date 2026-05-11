#!/usr/bin/env python3
import json
import re
from pathlib import Path

print("=== FIX PARSING HAL8_SOAL.TXT 30 UNIT ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def parse_hal8_soal(txt_path):
    """Parse hal8_soal.txt dengan benar"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except:
        return []

    lines = text.split("\n")
    soal_list = []
    current_soal = None
    current_number = None
    instruction_buffer = ""

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Detect question number (1. 2. 3. 4. 5.)
        match = re.match(r"^(\d+)\.\s*", line_stripped)
        if match:
            # Save previous soal
            if current_soal and current_number:
                if instruction_buffer:
                    current_soal["instruksi"] = instruction_buffer.strip()
                soal_list.append(current_soal)

            num = int(match.group(1))
            if num > 5:
                break

            current_number = num
            teks = line_stripped[match.end() :].strip()
            current_soal = {
                "nomor": num,
                "teks_soal": teks,
                "instruksi": "",
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
            }
            instruction_buffer = ""  # Reset instruction buffer
            continue

        if not current_soal:
            continue

        # Detect instruction patterns
        instr_patterns = [
            "[1~",
            "[2~",
            "[3~",
            "[4~",
            "[5~",
            "다음",
            "그림을",
            "문장을",
            "가장 알맞은",
            "다음은",
            "무엇에",
            "가장 알맞은",
        ]
        is_instruction = any(pat in line_stripped for pat in instr_patterns)

        # Detect choices
        if line_stripped.startswith("①"):
            current_soal["pilihan_a"] = line_stripped[1:].strip()
        elif line_stripped.startswith("②"):
            current_soal["pilihan_b"] = line_stripped[1:].strip()
        elif line_stripped.startswith("③"):
            current_soal["pilihan_c"] = line_stripped[1:].strip()
        elif line_stripped.startswith("④"):
            current_soal["pilihan_d"] = line_stripped[1:].strip()
        elif is_instruction:
            # This is instruction text
            if current_soal["instruksi"]:
                current_soal["instruksi"] += " " + line_stripped
            else:
                current_soal["instruksi"] = line_stripped
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

    return soal_list


# Process all 30 units
fixed_total = 0
updated_units = 0

for unit in range(31, 61):
    txt_path = base_dir / f"unit_{unit:02d}" / "teks" / "hal8_soal.txt"
    data_path = base_dir / f"unit_{unit:02d}" / "data.json"

    if not txt_path.exists() or not data_path.exists():
        continue

    # Parse hal8_soal.txt
    parsed = parse_hal8_soal(txt_path)
    if not parsed:
        continue

    # Load data.json
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    soal_list = data.get("soal", [])
    updated = 0

    # Update reading questions
    for soal in soal_list:
        if soal.get("tipe") != "membaca":
            continue

        nomor = soal.get("nomor")

        # Find matching parsed soal
        for p in parsed:
            if p["nomor"] == nomor:
                # Update fields
                if p["teks_soal"] and (
                    not soal.get("teks_soal")
                    or "①" in soal.get("teks_soal", "")
                    or soal.get("teks_soal", "").startswith("①")
                ):
                    soal["teks_soal"] = p["teks_soal"]

                if p["instruksi"]:
                    soal["instruksi"] = p["instruksi"]

                if p["pilihan_a"] and (
                    not soal.get("pilihan_a")
                    or soal.get("pilihan_a", "").strip() in ["①", "①"]
                ):
                    soal["pilihan_a"] = p["pilihan_a"]

                if p["pilihan_b"] and (
                    not soal.get("pilihan_b")
                    or soal.get("pilihan_b", "").strip() in ["②", "②"]
                ):
                    soal["pilihan_b"] = p["pilihan_b"]

                if p["pilihan_c"] and (
                    not soal.get("pilihan_c")
                    or soal.get("pilihan_c", "").strip() in ["③", "③"]
                ):
                    soal["pilihan_c"] = p["pilihan_c"]

                if p["pilihan_d"] and (
                    not soal.get("pilihan_d")
                    or soal.get("pilihan_d", "").strip() in ["④", "④"]
                ):
                    soal["pilihan_d"] = p["pilihan_d"]

                updated += 1
                break

    # Save if updated
    if updated > 0:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        fixed_total += updated
        updated_units += 1
        print(f"Unit {unit:02d}: {updated} soal diperbaiki")

print(f"\n=== SELESAI ===")
print(f"Total: {fixed_total} soal diperbaiki di {updated_units} unit")
