#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk rebuild data.json untuk 30 unit (31-60)
- Parse hal8_soal.txt (reading) dan hal9_soal.txt (listening)
- Tangani instruksi pattern [3~4] ...
- Bangun struktur JSON yang benar
"""

import json
import re
from pathlib import Path

print("=== REBUILD DATA.JSON 30 UNIT ===\n")

base_dir = Path("../assets/langit-korea-extracted")

# Load jawaban_all.json
jawaban_path = base_dir / "jawaban_all.json"
if jawaban_path.exists():
    with open(jawaban_path, "r", encoding="utf-8") as f:
        jawaban_data = json.load(f)
else:
    jawaban_data = {}
    print("⚠️ jawaban_all.json tidak ditemukan")


def parse_hal8_soal(txt_path):
    """Parse hal8_soal.txt - soal reading"""
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

    # Pola instruksi
    instr_patterns = [
        r"\[\d+~\d+\]",  # [3~4]
        r"다음 내용과 관계있는",
        r"다음 중",
        r"다음 글을",
        r"빈칸에 들어갈",
        r"가장 알맞은",
    ]

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
                "tipe": "membaca",
                "teks_soal": teks,
                "instruksi": "",
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
                "jawaban": "",
                "audio_teks": "",
                "ada_gambar_pilihan": False,
                "gambar_pilihan_a": None,
                "gambar_pilihan_b": None,
                "gambar_pilihan_c": None,
                "gambar_pilihan_d": None,
                "akses": "free" if num <= 18 else "premium",
            }
            instruction_buffer = ""
            continue

        if not current_soal:
            continue

        # Check if line is instruction
        is_instruction = any(re.search(pat, line_stripped) for pat in instr_patterns)

        # Detect choices
        if line_stripped.startswith("①"):
            # Extract text after ①
            text_choice = line_stripped[1:].strip()
            # Check if there are other symbols in same line
            for sym in ["②", "③", "④"]:
                idx = text_choice.find(sym)
                if idx != -1:
                    current_soal["pilihan_a"] = text_choice[:idx].strip()
                    # The rest might be other choices
                    break
            else:
                current_soal["pilihan_a"] = text_choice
            continue
        elif line_stripped.startswith("②"):
            text_choice = line_stripped[1:].strip()
            for sym in ["③", "④"]:
                idx = text_choice.find(sym)
                if idx != -1:
                    current_soal["pilihan_b"] = text_choice[:idx].strip()
                    break
            else:
                current_soal["pilihan_b"] = text_choice
            continue
        elif line_stripped.startswith("③"):
            text_choice = line_stripped[1:].strip()
            for sym in ["④"]:
                idx = text_choice.find(sym)
                if idx != -1:
                    current_soal["pilihan_c"] = text_choice[:idx].strip()
                    break
            else:
                current_soal["pilihan_c"] = text_choice
            continue
        elif line_stripped.startswith("④"):
            current_soal["pilihan_d"] = line_stripped[1:].strip()
            continue
        elif is_instruction:
            # This is instruction line
            if current_soal["instruksi"]:
                current_soal["instruksi"] += " " + line_stripped
            else:
                current_soal["instruksi"] = line_stripped
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

    return soal_list


def parse_hal9_soal(txt_path):
    """Parse hal9_soal.txt - soal listening"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except:
        return []

    # Split between soal and audio
    parts = re.split(r"듣기지문|지문", text)
    soal_part = parts[0] if len(parts) > 0 else text
    audio_part = parts[1] if len(parts) > 1 else ""

    lines = soal_part.split("\n")
    soal_list = []
    current_soal = None
    current_number = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Detect question number
        match = re.match(r"^(\d+)\.\s*", line_stripped)
        if match:
            if current_soal and current_number:
                soal_list.append(current_soal)

            num = int(match.group(1))
            if num > 5:
                break

            current_number = num
            teks = line_stripped[match.end() :].strip()
            current_soal = {
                "nomor": num,
                "tipe": "mendengarkan",
                "teks_soal": teks,
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
                "jawaban": "",
                "audio_teks": "",
                "ada_gambar_pilihan": False,
                "gambar_pilihan_a": None,
                "gambar_pilihan_b": None,
                "gambar_pilihan_c": None,
                "gambar_pilihan_d": None,
                "akses": "premium",
            }
            continue

        if not current_soal:
            continue

        # Detect choices
        if line_stripped.startswith("①"):
            current_soal["pilihan_a"] = line_stripped[1:].strip()
        elif line_stripped.startswith("②"):
            current_soal["pilihan_b"] = line_stripped[1:].strip()
        elif line_stripped.startswith("③"):
            current_soal["pilihan_c"] = line_stripped[1:].strip()
        elif line_stripped.startswith("④"):
            current_soal["pilihan_d"] = line_stripped[1:].strip()
        else:
            if current_soal["teks_soal"]:
                current_soal["teks_soal"] += " " + line_stripped
            else:
                current_soal["teks_soal"] = line_stripped

    if current_soal and current_number:
        soal_list.append(current_soal)

    # Parse audio
    if audio_part:
        audio_lines = audio_part.split("\n")
        audio_texts = []
        current_audio = ""
        for line in audio_lines:
            line = line.strip()
            if re.match(r"^\d+\.\s*", line):
                if current_audio:
                    audio_texts.append(current_audio.strip())
                current_audio = line[line.index(".") :].strip()
            else:
                current_audio += " " + line
        if current_audio:
            audio_texts.append(current_audio.strip())

        for i, soal in enumerate(soal_list):
            if i < len(audio_texts):
                soal["audio_teks"] = audio_texts[i]

    return soal_list


def update_jawaban(soal_list, unit_num):
    """Update jawaban from jawaban_all.json"""
    unit_jawaban = jawaban_data.get(str(unit_num), {})

    for soal in soal_list:
        tipe = soal["tipe"]
        nomor = str(soal["nomor"])

        if tipe == "membaca":
            jawaban = unit_jawaban.get("membaca", {}).get(nomor, "")
        else:
            jawaban = unit_jawaban.get("mendengarkan", {}).get(nomor, "")

        if jawaban:
            soal["jawaban"] = jawaban

    return soal_list


# Process all 30 units
rebuild_total = 0
updated_units = 0

for unit in range(31, 61):
    print(f"--- UNIT {unit:02d} ---")

    # Paths
    unit_dir = base_dir / f"unit_{unit:02d}"
    data_path = unit_dir / "data.json"
    txt_dir = unit_dir / "teks"

    # Parse hal8_soal.txt (reading)
    txt8_path = txt_dir / "hal8_soal.txt"
    reading = []
    if txt8_path.exists():
        reading = parse_hal8_soal(txt8_path)
        print(f"  Reading: {len(reading)} soal")

    # Parse hal9_soal.txt (listening)
    txt9_path = txt_dir / "hal9_soal.txt"
    listening = []
    if txt9_path.exists():
        listening = parse_hal9_soal(txt9_path)
        print(f"  Listening: {len(listening)} soal")

    # Combine
    all_soal = reading + listening

    if not all_soal:
        print(f"  Tidak ada soal\n")
        continue

    # Update jawaban
    all_soal = update_jawaban(all_soal, unit)

    # Load existing data.json to preserve other fields (unit info, halaman, etc.)
    if data_path.exists():
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}

    # Preserve unit info
    if "unit" not in data:
        data["unit"] = unit
    if "title_ko" not in data:
        # Try to get from PDF filename
        pass  # We'll skip for now

    # Replace soal array
    data["soal"] = all_soal

    # Save
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    rebuild_total += len(all_soal)
    updated_units += 1
    print(f"  ✅ {len(all_soal)} soal direbuild\n")

print("=== SELESAI ===")
print(f"Total: {rebuild_total} soal direbuild di {updated_units} unit")
