#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script perbaikan parsing FINAL:
1. Fix parsing pilihan yang tergabung (misal: "올리다 ④ 내리다")
2. Instruksi [X~Y] ditempelkan ke soal X sampai Y
3. Handle pilihan kosong
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== FIX PARSING FINAL - LANGIT KOREA ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def parse_soal_txt_final(txt_path, tipe="membaca", unit_num=31):
    """
    Parse dengan logika yang lebih teliti untuk memisahkan pilihan
    """
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return []

    lines = text.split("\n")
    soal_dict = {}
    current_num = None
    pending_instruction = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header
        if re.match(r"^(읽기|듣기)\s+(READING|LISTENING)", line_stripped):
            continue

        # Check if this line is an instruction with [X~Y] pattern
        instr_match = re.match(r"^\[(\d+)~(\d+)\]\s*(.*)", line_stripped)
        if instr_match:
            start_num = int(instr_match.group(1))
            end_num = int(instr_match.group(2))
            instr_text = instr_match.group(3).strip()
            if not instr_text:
                instr_text = f"[{start_num}~{end_num}] 빈칸에 들어갈 가장 알맞은 것을 고르십시오."
            pending_instruction = (start_num, end_num, instr_text)
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
                if num >= end:
                    pending_instruction = None

            current_num = num
            continue

        if current_num is None:
            continue

        current_soal = soal_dict[current_num]

        # Detect choices - handle lines with ① ② ③ ④
        # Pattern: pilihan bisa sebar di beberapa line
        choice_symbols = ["①", "②", "③", "④"]

        # Check if line contains any choice symbol
        has_choice = any(sym in line_stripped for sym in choice_symbols)

        if has_choice:
            # Parse this line for choices
            # We need to extract text for each choice symbol found
            temp_line = line_stripped

            for i, sym in enumerate(choice_symbols):
                if sym in temp_line:
                    # Get text after this symbol
                    idx = temp_line.index(sym)
                    rest = temp_line[idx + len(sym) :]

                    # Remove any subsequent choice symbols from rest
                    for next_sym in choice_symbols[i + 1 :]:
                        if next_sym in rest:
                            rest = rest[: rest.index(next_sym)]

                    rest = rest.strip()

                    # Assign to correct pilihan
                    key = ["a", "b", "c", "d"][i]
                    current_soal[f"pilihan_{key}"] = rest

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
        s["id"] = f"u{unit_num}_{prefix}{s['nomor']}"
        s["jawaban"] = ""
        s["audio_teks"] = ""
        s["ada_gambar_pilihan"] = False
        s["gambar_pilihan"] = {}
        s["akses"] = "free"

    return soal_list


def update_all_units_final():
    """Update all 30 units with correct parsing"""
    success_count = 0
    failed_units = []
    laporan = {}

    for unit_num in range(31, 61):
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
            reading_soal = parse_soal_txt_final(hal8_path, "membaca", unit_num)

        # Parse listening
        hal9_path = teks_dir / "hal9_soal.txt"
        listening_soal = []
        if hal9_path.exists():
            listening_soal = parse_soal_txt_final(hal9_path, "mendengarkan", unit_num)

        if not reading_soal and not listening_soal:
            print("tidak ada soal")
            failed_units.append(unit_num)
            continue

        # Create data.json
        data = {
            "unit": unit_num,
            "title_ko": "",
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
success, failed, laporan = update_all_units_final()

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success}/30")
print(f"Gagal: {len(failed)}")
if failed:
    print(f"  Unit gagal: {failed}")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_final.json"
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

# Verify one unit
print("\n=== VERIFIKASI UNIT 31 ===")
data_path = base_dir / "unit_31" / "data.json"
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for soal in data["soal"][:5]:  # First 5 reading questions
    print(f"\nSoal {soal['nomor']} ({soal['tipe']}):")
    print(f"  Teks: {soal['teks_soal'][:50]}...")
    print(f"  Instruksi: {soal['instruksi']}")
    print(f"  A: {soal['pilihan_a']}")
    print(f"  B: {soal['pilihan_b']}")
    print(f"  C: {soal['pilihan_c']}")
    print(f"  D: {soal['pilihan_d']}")

print("\n=== SELESAI ===")
