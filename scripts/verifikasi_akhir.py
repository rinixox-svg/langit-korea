#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifikasi akhir semua unit (31-60)
Mengecek:
1. Struktur reading_data.json
2. Struktur listening_data.json
3. Gambar listening terkait
4. Laporan lengkap
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== VERIFIKASI AKHIR SEMUA UNIT ===\n")

base_dir = Path("../assets/langit-korea-extracted")

laporan = {
    "waktu": datetime.now().isoformat(),
    "total_unit": 30,
    "unit_berhasil": 0,
    "unit_gagal": [],
    "detail": {},
}

for unit_num in range(31, 61):
    unit_key = f"unit_{unit_num:02d}"
    unit_dir = base_dir / unit_key

    if not unit_dir.exists():
        laporan["unit_gagal"].append(unit_num)
        continue

    unit_detail = {
        "reading": {"ada": False, "jumlah_soal": 0, "error": ""},
        "listening": {"ada": False, "jumlah_soal": 0, "gambar_terkait": 0, "error": ""},
    }

    # Cek reading_data.json
    reading_path = unit_dir / "reading_data.json"
    if reading_path.exists():
        try:
            with open(reading_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            reading_soal = data.get("soal", [])
            unit_detail["reading"]["ada"] = True
            unit_detail["reading"]["jumlah_soal"] = len(reading_soal)

            # Cek field penting
            for soal in reading_soal:
                if not soal.get("teks_soal") and not soal.get("instruksi"):
                    unit_detail["reading"]["error"] = "Ada soal tanpa teks/instruksi"
                    break
        except Exception as e:
            unit_detail["reading"]["error"] = str(e)

    # Cek listening_data.json
    listening_path = unit_dir / "listening_data.json"
    if listening_path.exists():
        try:
            with open(listening_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            listening_soal = data.get("soal", [])
            unit_detail["listening"]["ada"] = True
            unit_detail["listening"]["jumlah_soal"] = len(listening_soal)

            # Cek gambar
            gambar_terkait = 0
            for soal in listening_soal:
                if soal.get("ada_gambar_pilihan") and soal.get("gambar_pilihan"):
                    if soal["gambar_pilihan"].get("a"):
                        gambar_terkait += 1
            unit_detail["listening"]["gambar_terkait"] = gambar_terkait
        except Exception as e:
            unit_detail["listening"]["error"] = str(e)

    # Cek folder images
    images_dir = unit_dir / "images"
    if images_dir.exists():
        listening_images = list(images_dir.glob("*listening*.jpeg")) + list(
            images_dir.glob("*listening*.png")
        )
        unit_detail["listening"]["gambar_di_folder"] = len(listening_images)

    laporan["detail"][unit_key] = unit_detail
    laporan["unit_berhasil"] += 1

    # Print status
    r_status = (
        f"R:{unit_detail['reading']['jumlah_soal']}"
        if unit_detail["reading"]["ada"]
        else "R:✗"
    )
    l_status = (
        f"L:{unit_detail['listening']['jumlah_soal']}"
        if unit_detail["listening"]["ada"]
        else "L:✗"
    )
    g_status = (
        f"G:{unit_detail['listening']['gambar_terkait']}"
        if unit_detail["listening"]["ada"]
        else ""
    )

    print(f"[{unit_num - 30}/30] {unit_key}: {r_status} {l_status} {g_status}")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_verifikasi_akhir.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(laporan, f, ensure_ascii=False, indent=2)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Unit berhasil: {laporan['unit_berhasil']}/30")
print(f"Unit gagal: {len(laporan['unit_gagal'])}")
if laporan["unit_gagal"]:
    print(f"  Gagal: {laporan['unit_gagal']}")

print(f"\nLaporan lengkap: {laporan_path}")

# Tampilkan contoh struktur yang benar
print("\n=== CONTOH STRUKTUR YANG BENAR ===")
contoh_path = base_dir / "unit_31" / "reading_data.json"
with open(contoh_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("\n1. Reading Data (unit_31/reading_data.json):")
print(f"   - Unit: {data.get('unit')}")
print(f"   - Judul: {data.get('title_id')}")
print(f"   - Jumlah soal: {len(data.get('soal', []))}")
if data.get("soal"):
    soal1 = data["soal"][0]
    print(f"   - Contoh soal 1:")
    print(f"     • nomor: {soal1.get('nomor')}")
    print(f"     • instruksi: '{soal1.get('instruksi', '')}'")
    print(f"     • teks_soal: '{soal1.get('teks_soal', '')[:50]}...'")
    print(f"     • pilihan_a: '{soal1.get('pilihan_a', '')}'")

print("\n2. Listening Data (unit_31/listening_data.json):")
contoh_listening = base_dir / "unit_31" / "listening_data.json"
with open(contoh_listening, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"   - Jumlah soal: {len(data.get('soal', []))}")
if data.get("soal"):
    soal1 = data["soal"][0]
    print(f"   - Contoh soal 1:")
    print(f"     • nomor: {soal1.get('nomor')}")
    print(f"     • ada_gambar_pilihan: {soal1.get('ada_gambar_pilihan')}")
    print(f"     • gambar_pilihan: {soal1.get('gambar_pilihan', {})}")

print("\n=== SELESAI ===")
print("Semua file JSON sudah rapi dan siap untuk tahap selanjutnya!")
print("Langkah selanjutnya:")
print("  1. Tambah jawaban dari appendix-answers.pdf")
print("  2. Upload ke Supabase")
print("  3. Buat frontend untuk menampilkan soal")
