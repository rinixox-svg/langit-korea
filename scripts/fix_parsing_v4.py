#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script perbaikan FINAL dengan logika yang lebih teliti:
1. Deteksi instruksi di awal teks soal (seperti "다음 중...", "다음 글을...")
2. Pisahkan instruksi ke field 'instruksi'
3. Handle pola [X~Y] dengan benar
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== FIX PARSING FINAL - PISAHKAN INSTRUKSI ===\n")

base_dir = Path("../assets/langit-korea-extracted")

# Pola instruksi yang umum
INSTRUCTION_PATTERNS = [
    r"다음 단어의 반대말은 무엇입니까\?",
    r"다음 중 밑줄 친 부분이 맞는 문장을 고르십시오\.",
    r"다음 글을 읽고 내용과 같은 것을 고르십시오\.",
    r"다음 내용과 관계있는 그림을 고르십시오\.",
    r"다음 그림과 관계있는 내용은 무엇입니까\?",
    r"다음은 무엇에 대한 설명입니까\?",
    r"빈칸에 들어갈 가장 알맞은 것을 고르십시오\.",
    r"빈칸에 들어갈 알맞은 단어를 고르십시오\.",
    r"빈칸에 들어갈 알맞은 표현을 골라 문장을 완성하십시오\.",
]


def is_instruction_line(line):
    """Cek apakah baris adalah instruksi"""
    for pat in INSTRUCTION_PATTERNS:
        if re.search(pat, line):
            return True
    # Cek pola umum
    if "고르십시오" in line or "완성하십시오" in line:
        return True
    return False


def parse_soal_final_v4(txt_path, tipe="membaca", unit_num=31):
    """Parse dengan memisahkan instruksi dari teks soal"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return []

    lines = text.split("\n")
    soal_dict = {}
    current_num = None
    pending_instruction = None
    global_instruction = ""  # Instruksi di awal file

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header
        if re.match(r"^(읽기|듣기)\s+(READING|LISTENING)", line_stripped):
            continue

        # Cek [X~Y] pattern
        instr_match = re.match(r"^\[(\d+)~(\d+)\]\s*(.*)", line_stripped)
        if instr_match:
            start_num = int(instr_match.group(1))
            end_num = int(instr_match.group(2))
            instr_text = instr_match.group(3).strip()
            if not instr_text:
                instr_text = "빈칸에 들어갈 가장 알맞은 것을 고르십시오."
            pending_instruction = (start_num, end_num, instr_text)
            continue

        # Detect question number
        match = re.match(r"^(\d+)\.\s*", line_stripped)
        if match:
            num = int(match.group(1))
            if num > 5:
                break

            teks = line_stripped[match.end() :].strip()

            # Cek apakah teks mengandung instruksi di awal
            instruksi_soal = ""
            for pat in INSTRUCTION_PATTERNS:
                m = re.match(pat, teks)
                if m:
                    instruksi_soal = m.group(0)
                    # Hapus instruksi dari teks soal
                    teks = teks[m.end() :].strip()
                    break

            # Jika tidak ketemu pola spesifik, cek manual
            if not instruksi_soal:
                # Cek apakah ada "고르십시오" di awal teks
                idx = teks.find("고르십시오")
                if idx != -1:
                    # Cari awal kalimat (dari awal sampai setelah 고르십시오)
                    end_instr = idx + len("고르십시오")
                    # Pastikan ini di awal teks (dalam 50 karakter pertama)
                    if idx < 50:
                        instruksi_soal = teks[:end_instr].strip()
                        teks = teks[end_instr:].strip()

            # Create soal entry
            soal_dict[num] = {
                "nomor": num,
                "tipe": tipe,
                "teks_soal": teks,
                "instruksi": instruksi_soal,
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
            }

            # Apply pending instruction [X~Y]
            if pending_instruction:
                start, end, instr = pending_instruction
                if start <= num <= end:
                    # Jika soal sudah punya instruksi, jangan timpa
                    if not soal_dict[num]["instruksi"]:
                        soal_dict[num]["instruksi"] = instr
                if num >= end:
                    pending_instruction = None

            current_num = num
            continue

        if current_num is None:
            # Baris sebelum soal pertama - mungkin instruksi global
            if is_instruction_line(line_stripped):
                global_instruction = line_stripped
            continue

        current_soal = soal_dict[current_num]

        # Detect choices
        choice_symbols = ["①", "②", "③", "④"]
        has_choice = any(sym in line_stripped for sym in choice_symbols)

        if has_choice:
            for i, sym in enumerate(choice_symbols):
                if sym in line_stripped:
                    idx = line_stripped.index(sym)
                    rest = line_stripped[idx + len(sym) :]
                    # Remove subsequent choice symbols
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

    # Convert to list
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


def update_all_units_v4():
    """Update semua 30 unit dengan parsing v4"""
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
            reading_soal = parse_soal_final_v4(hal8_path, "membaca", unit_num)

        # Parse listening
        hal9_path = teks_dir / "hal9_soal.txt"
        listening_soal = []
        if hal9_path.exists():
            listening_soal = parse_soal_final_v4(hal9_path, "mendengarkan", unit_num)

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

        # Preserve metadata
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
success, failed, laporan = update_all_units_v4()

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success}/30")
print(f"Gagal: {len(failed)}")
if failed:
    print(f"  Unit gagal: {failed}")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_v4.json"
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

# Verifikasi cepat
print("\n=== VERIFIKASI UNIT 31 (MEMBACA) ===")
data_path = base_dir / "unit_31" / "data.json"
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for soal in data["soal"][:5]:
    if soal["tipe"] != "membaca":
        continue
    print(f"\nSoal {soal['nomor']}:")
    print(f"  Instruksi: '{soal['instruksi']}'")
    print(f"  Teks: {soal['teks_soal'][:60]}...")
    print(f"  A: {soal['pilihan_a']}")
    print(f"  B: {soal['pilihan_b']}")
    print(f"  C: {soal['pilihan_c']}")
    print(f"  D: {soal['pilihan_d']}")

print("\n=== SELESAI ===")
