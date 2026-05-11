#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script perbaikan parsing v2:
1. Instruksi [X~Y] ditempelkan ke soal X sampai Y
2. Pilihan ①②③④ dipisahkan dengan benar
3. Handle multi-line choices
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== FIX PARSING V2 - LANGIT KOREA ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def parse_soal_txt_v2(txt_path, tipe="membaca"):
    """
    Parse dengan logika:
    - Track current instruction
    - If instruction has [X~Y] pattern, apply to questions X-Y
    - Parse choices correctly
    """
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"    Error reading {txt_path}: {e}")
        return []

    lines = text.split("\n")

    # Structure: {nomor: {soal_data}}
    soal_dict = {}
    current_num = None
    current_instr = ""
    pending_instruction = None  # (start_num, end_num, instruction_text)

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header
        if re.match(r"^(읽기|듣기)\s+(READING|LISTENING)", line_stripped):
            continue

        # Check if this line is an instruction with [X~Y] pattern
        instr_match = re.match(r"^\[(\d+)~(\d+)\](.*)", line_stripped)
        if instr_match:
            start_num = int(instr_match.group(1))
            end_num = int(instr_match.group(2))
            instr_text = instr_match.group(3).strip()
            pending_instruction = (start_num, end_num, instr_text)
            continue

        # Check if line contains instruction keywords (without [X~Y])
        if not re.match(r"^\d+\.", line_stripped):
            instr_keywords = ["고르십시오", "알맞은", "들고", "읽고"]
            if any(kw in line_stripped for kw in instr_keywords):
                current_instr = line_stripped
                continue

        # Detect question number
        match = re.match(r"^(\d+)\.\s*", line_stripped)
        if match:
            num = int(match.group(1))
            if num > 5:
                break

            teks = line_stripped[match.end() :].strip()

            # Create soal entry
            soal_dict[num] = {
                "nomor": num,
                "tipe": tipe,
                "teks_soal": teks,
                "instruksi": "",
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
            }

            # Check if there's pending instruction for this question
            if pending_instruction:
                start, end, instr = pending_instruction
                if start <= num <= end:
                    soal_dict[num]["instruksi"] = instr
                # If we've passed the range, clear pending
                if num > end:
                    pending_instruction = None
            elif current_instr:
                soal_dict[num]["instruksi"] = current_instr
                current_instr = ""  # Clear after use

            current_num = num
            continue

        if current_num is None:
            continue

        current_soal = soal_dict[current_num]

        # Detect choices - handle lines with ① ② ③ ④
        if "①" in line_stripped:
            # Parse all choices from this line
            # Replace Korean circled numbers with markers for easier parsing
            test_line = line_stripped
            for sym, key in [("①", "a"), ("②", "b"), ("③", "c"), ("④", "d")]:
                if sym in test_line:
                    parts = test_line.split(sym, 1)
                    if len(parts) > 1:
                        # Get text after this symbol
                        choice_text = parts[1].strip()
                        # Remove any subsequent choice symbols from this choice
                        for next_sym in ["①", "②", "③", "④"]:
                            if next_sym in choice_text:
                                choice_text = choice_text.split(next_sym)[0].strip()
                        current_soal[f"pilihan_{key}"] = choice_text
                        test_line = parts[1]  # Continue with rest for next symbol
            continue

        # Handle individual choice lines
        if line_stripped.startswith("②"):
            current_soal["pilihan_b"] = line_stripped[1:].strip()
            continue
        elif line_stripped.startswith("③"):
            current_soal["pilihan_c"] = line_stripped[1:].strip()
            continue
        elif line_stripped.startswith("④"):
            current_soal["pilihan_d"] = line_stripped[1:].strip()
            continue

        # Continuation of question text
        if current_soal["teks_soal"]:
            current_soal["teks_soal"] += " " + line_stripped
        else:
            current_soal["teks_soal"] = line_stripped

    # Convert dict to list, sorted by nomor
    soal_list = [soal_dict[num] for num in sorted(soal_dict.keys())]

    # Add IDs and other fields
    prefix = "m" if tipe == "membaca" else "l"
    for s in soal_list:
        s["id"] = f"u{31}_{prefix}{s['nomor']}"  # Will be updated with correct unit
        s["jawaban"] = ""
        s["audio_teks"] = ""
        s["ada_gambar_pilihan"] = False
        s["gambar_pilihan"] = {}
        s["akses"] = "free"

    return soal_list


def update_all_units():
    """Update all 30 units with correct parsing"""
    UNITS = list(range(31, 61))

    success_count = 0
    failed_units = []
    laporan = {}

    for unit_num in UNITS:
        print(f"[{unit_num - 30}/30] Unit {unit_num:02d}...", end=" ")

        unit_dir = base_dir / f"unit_{unit_num:02d}"
        if not unit_dir.exists():
            print("directory tidak ada")
            failed_units.append(unit_num)
            continue

        teks_dir = unit_dir / "teks"
        if not teks_dir.exists():
            print("teks directory tidak ada")
            failed_units.append(unit_num)
            continue

        # Parse reading
        hal8_path = teks_dir / "hal8_soal.txt"
        reading_soal = []
        if hal8_path.exists():
            reading_soal = parse_soal_txt_v2(hal8_path, "membaca")
            # Fix IDs
            for s in reading_soal:
                s["id"] = f"u{unit_num}_m{s['nomor']}"

        # Parse listening
        hal9_path = teks_dir / "hal9_soal.txt"
        listening_soal = []
        if hal9_path.exists():
            listening_soal = parse_soal_txt_v2(hal9_path, "mendengarkan")
            # Fix IDs
            for s in listening_soal:
                s["id"] = f"u{unit_num}_l{s['nomor']}"

        if not reading_soal and not listening_soal:
            print("tidak ada soal")
            failed_units.append(unit_num)
            continue

        # Create data.json
        data = {
            "unit": unit_num,
            "title_ko": "",  # Will be filled from existing data if available
            "title_id": "",
            "file": f"unit_{unit_num:02d}.pdf",
            "total_halaman": 10,
            "soal": reading_soal + listening_soal,
        }

        # Try to preserve existing metadata
        data_path = unit_dir / "data.json"
        if data_path.exists():
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    data["title_ko"] = old_data.get("title_ko", "")
                    data["title_id"] = old_data.get("title_id", "")
                    data["file"] = old_data.get("file", data["file"])
            except:
                pass

        # Save
        try:
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ (R:{len(reading_soal)}, L:{len(listening_soal)})")
            success_count += 1
            laporan[unit_num] = {
                "reading": len(reading_soal),
                "listening": len(listening_soal),
            }
        except Exception as e:
            print(f"✗ ({e})")
            failed_units.append(unit_num)

    return success_count, failed_units, laporan


# Run
success, failed, laporan = update_all_units()

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success}/30")
print(f"Gagal: {len(failed)}")
if failed:
    print(f"  Unit gagal: {failed}")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_v2.json"
with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "berhasil": success,
            "gagal": failed,
            "detail": laporan,
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
