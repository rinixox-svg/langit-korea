#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script perbaikan listening soal:
1. Parse hal9_soal.txt dengan benar
2. Tandai 'ada_gambar_pilihan': True untuk listening
3. Simpan audio script dari bagian '듣기지문'
"""

import json
import re
from pathlib import Path

print("=== FIX LISTENING SOAL - GAMBAR PILIHAN ===\n")

base_dir = Path("../assets/langit-korea-extracted")


def parse_listening_with_script(txt_path, unit_num):
    """
    Parse hal9_soal.txt untuk listening
    - Teks soal = pertanyaan
    - Pilihan = gambar (④ ① ② ③) -> tandai ada_gambar_pilihan=True
    - Audio script = bagian '듣기지문'
    """
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"    Error: {e}")
        return [], ""

    # Pisahkan bagian soal dan audio script
    parts = text.split("듣기지문")
    soal_text = parts[0] if len(parts) > 0 else text
    audio_script = parts[1].strip() if len(parts) > 1 else ""

    lines = soal_text.split("\n")
    soal_list = []
    current_soal = None
    current_num = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header
        if re.match(r"^듣기\s+LISTENING", line_stripped):
            continue

        # Detect question number
        match = re.match(r"^(\d+)\.\s*", line_stripped)
        if match:
            # Save previous soal
            if current_soal and current_num:
                soal_list.append(current_soal)

            num = int(match.group(1))
            if num > 5:
                break

            teks = line_stripped[match.end() :].strip()

            current_soal = {
                "nomor": num,
                "tipe": "mendengarkan",
                "teks_soal": teks,
                "instruksi": "",
                "pilihan_a": "①",  # Placeholder untuk gambar
                "pilihan_b": "②",
                "pilihan_c": "③",
                "pilihan_d": "④",
                "id": f"u{unit_num}_l{num}",
                "jawaban": "",
                "audio_teks": "",  # Will be filled with audio_script
                "ada_gambar_pilihan": True,  # Listening pilihan = gambar
                "gambar_pilihan": {},  # Will be filled later from PDF images
                "akses": "free",
            }
            current_num = num
            continue

        if not current_soal:
            continue

        # If line contains only symbols ① ② ③ ④, skip (it's just placeholder)
        if re.match(r"^[①②③④\s]+$", line_stripped):
            continue

        # Otherwise, it's continuation of question text
        if current_soal["teks_soal"]:
            current_soal["teks_soal"] += " " + line_stripped
        else:
            current_soal["teks_soal"] = line_stripped

    # Save last soal
    if current_soal and current_num:
        soal_list.append(current_soal)

    return soal_list, audio_script


def update_all_listening():
    """Update semua unit dengan listening soal yang benar"""
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

        # Parse listening
        hal9_path = teks_dir / "hal9_soal.txt"
        if not hal9_path.exists():
            print("hal9 tidak ada")
            failed_units.append(unit_num)
            continue

        listening_soal, audio_script = parse_listening_with_script(hal9_path, unit_num)

        if not listening_soal:
            print("tidak ada soal")
            failed_units.append(unit_num)
            continue

        # Update audio_teks for all soal in this unit
        for soal in listening_soal:
            soal["audio_teks"] = audio_script

        # Simpan ke listening_data.json
        listening_data = {
            "unit": unit_num,
            "title_ko": "",
            "title_id": "",
            "file": f"unit_{unit_num:02d}.pdf",
            "total_halaman": 10,
            "soal": listening_soal,
        }

        # Preserve metadata if exists
        data_path = unit_dir / "data.json"
        if data_path.exists():
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    listening_data["title_ko"] = old_data.get("title_ko", "")
                    listening_data["title_id"] = old_data.get("title_id", "")
                    listening_data["file"] = old_data.get(
                        "file", listening_data["file"]
                    )
            except:
                pass

        # Save listening_data.json
        listening_path = unit_dir / "listening_data.json"
        try:
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(listening_data, f, ensure_ascii=False, indent=2)
            print(f"✓ ({len(listening_soal)} soal, audio: {len(audio_script)} chars)")
            success_count += 1
            laporan[unit_num] = {
                "listening": len(listening_soal),
                "audio_script_length": len(audio_script),
            }
        except Exception as e:
            print(f"✗ ({e})")
            failed_units.append(unit_num)

    return success_count, failed_units, laporan


# Run
success, failed, laporan = update_all_listening()

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success}/30")
print(f"Gagal: {len(failed)}")
if failed:
    print(f"  Unit gagal: {failed}")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_listening_fix.json"
with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "berhasil": success,
            "gagal": failed,
            "detail": laporan,
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")

# Verifikasi Unit 31
print("\n=== VERIFIKASI UNIT 31 LISTENING ===")
data_path = base_dir / "unit_31" / "listening_data.json"
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for soal in data["soal"]:
    print(f"\nSoal {soal['nomor']}:")
    print(f"  Teks: {soal['teks_soal'][:60]}...")
    print(
        f"  Pilihan: A={soal['pilihan_a']}, B={soal['pilihan_b']}, C={soal['pilihan_c']}, D={soal['pilihan_d']}"
    )
    print(f"  Ada gambar: {soal['ada_gambar_pilihan']}")
    print(f"  Audio teks (first 100 chars): {soal['audio_teks'][:100]}...")

print("\n=== SELESAI ===")
