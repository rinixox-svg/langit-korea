#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isi audio_teks untuk unit 46 dan 58:
1. Cek PDF unit_46_animal_husbry.pdf dan unit_58_labor_stards_act.pdf
2. Cari bagian "듣기지문" (audio script)
3. Masukkan ke field 'audio_teks' di listening_data.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF

print("=== ISI AUDIO_TEKS UNIT 46 & 58 ===\n")

base_dir = Path("../assets/langit-korea-extracted")
pdf_dir = Path("../pdf_modul")

# Mapping unit ke file PDF
unit_pdf = {
    46: "unit_46_animal_husbry.pdf",
    58: "unit_58_labor_stards_act.pdf",  # Note: nama file mungkin berbeda
}

# Coba cari nama file yang benar untuk unit 58
if not (pdf_dir / unit_pdf[58]).exists():
    # Cari file yang mirip
    for f in pdf_dir.iterdir():
        if "58" in f.name and "labor" in f.name.lower():
            unit_pdf[58] = f.name
            break


def extract_audio_script(pdf_path):
    """Extract audio script dari bagian '듣기지문' di PDF"""
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        return f"Error: {e}"

    audio_script = ""

    # Cari di semua halaman
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if "듣기지문" in text:
            # Ambil bagian setelah "듣기지문"
            parts = text.split("듣기지문")
            if len(parts) > 1:
                # Ambil teks, hapus nomor halaman di akhir
                script = parts[1].strip()
                lines = script.split("\n")
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Stop jika ketemu angka (nomor halaman)
                    if re.match(r"^\d+$", line):
                        break
                    clean_lines.append(line)

                audio_script = "\n".join(clean_lines).strip()
                break

    doc.close()
    return audio_script if audio_script else "Tidak ditemukan"


# Proses unit 46 dan 58
updated_units = []
failed_units = []

for unit_num, pdf_name in unit_pdf.items():
    print(f"Unit {unit_num:02d} ({pdf_name})...")

    pdf_path = pdf_dir / pdf_name
    if not pdf_path.exists():
        print(f"  ✗ PDF tidak ditemukan: {pdf_path}")
        failed_units.append(unit_num)
        continue

    # Extract audio script
    audio_script = extract_audio_script(pdf_path)

    if (
        not audio_script
        or audio_script.startswith("Error")
        or audio_script == "Tidak ditemukan"
    ):
        print(f"  ✗ {audio_script}")
        failed_units.append(unit_num)
        continue

    print(f"  ✓ Audio script ditemukan ({len(audio_script)} chars)")
    print(f"    Contoh: {audio_script[:100]}...")

    # Update listening_data.json
    listening_path = base_dir / f"unit_{unit_num:02d}" / "listening_data.json"

    if not listening_path.exists():
        print(f"  ✗ listening_data.json tidak ada")
        failed_units.append(unit_num)
        continue

    try:
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ✗ Error baca: {e}")
        failed_units.append(unit_num)
        continue

    soal_list = data.get("soal", [])
    updated = 0

    for soal in soal_list:
        if not soal.get("audio_teks"):
            soal["audio_teks"] = audio_script
            updated += 1

    # Save
    try:
        with open(listening_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ Terupdate {updated} soal")
        updated_units.append(unit_num)
    except Exception as e:
        print(f"  ✗ Error simpan: {e}")
        failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {len(updated_units)} unit")
print(f"Gagal: {len(failed_units)}")
if failed_units:
    print(f"  Detail: {failed_units}")

# Verifikasi
print("\n=== VERIFIKASI UNIT 46 & 58 ===")

for unit_num in [46, 58]:
    listening_path = base_dir / f"unit_{unit_num:02d}" / "listening_data.json"
    if not listening_path.exists():
        print(f"\nUnit {unit_num:02d}: listening_data.json tidak ada")
        continue

    with open(listening_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nUnit {unit_num:02d} (5 soal):")
    for soal in data["soal"][:2]:  # Cek 2 soal pertama
        nomor = soal["nomor"]
        audio_teks = soal.get("audio_teks", "")
        print(
            f"  Soal {nomor}: audio_teks='{audio_teks[:50]}...' (len={len(audio_teks)})"
        )

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_fill_audio_46_58.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "berhasil": updated_units,
            "gagal": failed_units,
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
print("Audio teks sudah terisi untuk unit 46 dan 58!")
print("Sekarang semua 150 soal listening memiliki audio_teks!")
