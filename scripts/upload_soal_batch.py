#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Upload Soal ke Supabase - Langit Korea
Hanya upload soal (tanpa MP3 upload karena sudah ada)
"""

import json
from datetime import datetime
from pathlib import Path

from supabase import create_client

print("=== UPLOAD SOAL KE SUPABASE ===\n")

# ========== KONFIGURASI ==========
SUPABASE_URL = "https://mozmuwrkfsipzfupybwh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vem11d3JrZnNpcHpmdXB5YndoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzY5NTk1NCwiZXhwIjoyMDkzMjcxOTU0fQ.SZSNk6xV-vq17beo_LwWzsZSp9UVGdqfR-R35cGxawE"
# ========== ========== ==========

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== 1. KUMPULKAN SEMUA SOAL ==========
print("[1] Mengumpulkan soal dari JSON files...")
base_dir = Path("../assets/langit-korea-extracted")
all_soal = []

for unit_num in range(31, 61):
    unit_dir = base_dir / f"unit_{unit_num:02d}"

    if not unit_dir.exists():
        continue

    # Reading
    reading_path = unit_dir / "reading_data.json"
    if reading_path.exists():
        with open(reading_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for soal in data.get("soal", []):
            soal["bab"] = unit_num
            soal["tipe"] = "membaca"
            if not soal.get("teks_soal") and soal.get("instruksi"):
                soal["teks_soal"] = soal["instruksi"]
            all_soal.append(soal)

    # Listening
    listening_path = unit_dir / "listening_data.json"
    if listening_path.exists():
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for soal in data.get("soal", []):
            soal["bab"] = unit_num
            soal["tipe"] = "mendengarkan"
            if not soal.get("teks_soal") and soal.get("instruksi"):
                soal["teks_soal"] = soal["instruksi"]
            all_soal.append(soal)

print(f"[OK] Total soal: {len(all_soal)}")

# ========== 2. KONVERSI KE FORMAT DB ==========
print("\n[2] Konversi ke format database...")


def convert_to_db(soal, index):
    # ID menggunakan integer (auto increment di DB)
    # Kita pakai index sebagai ID sementara

    jawaban = soal.get("jawaban", "")
    if jawaban not in ["a", "b", "c", "d"]:
        jawaban = None

    akses = "free" if soal["bab"] <= 48 else "premium"

    return {
        "id": index,  # Gunakan integer index
        "unit": soal["bab"],
        "tipe": soal["tipe"],
        "teks_soal": soal.get("teks_soal", ""),
        "teks_soal_id": soal.get("instruksi", ""),
        "audio_url": soal.get("audio_url", ""),
        "audio_teks": soal.get("audio_teks", ""),
        "pilihan_a": soal.get("pilihan_a", ""),
        "pilihan_b": soal.get("pilihan_b", ""),
        "pilihan_c": soal.get("pilihan_c", ""),
        "pilihan_d": soal.get("pilihan_d", ""),
        "jawaban": jawaban,
        "penjelasan": soal.get("penjelasan", ""),
        "tingkat": soal.get("tingkat", "sedang"),
        "ada_gambar_pilihan": soal.get("ada_gambar_pilihan", False),
        "akses": akses,
    }


db_data = []
skipped = []

for i, s in enumerate(all_soal):
    jawaban = s.get("jawaban", "")
    if jawaban not in ["a", "b", "c", "d"]:
        skipped.append(
            f"u{s['bab']}_{'m' if s['tipe'] == 'membaca' else 'l'}{s.get('nomor', '?')}"
        )
        continue
    db_data.append(convert_to_db(s, len(db_data) + 1))  # ID incremental

print(f"[OK] Data siap: {len(db_data)} baris")
print(f"[INFO] Diskip: {len(skipped)} soal (tanpa jawaban)")
if skipped:
    print(f"  Skip: {skipped}")

# ========== 3. UPLOAD DENGAN UPSERT ==========
print("\n[3] Upload ke Supabase (upsert)...")

try:
    # Batch upload (50 per batch untuk menghindari timeout)
    batch_size = 50
    total_uploaded = 0

    for i in range(0, len(db_data), batch_size):
        batch = db_data[i : i + batch_size]
        response = supabase.table("soal_eps").upsert(batch).execute()
        total_uploaded += len(response.data)
        print(f"  Batch {i // batch_size + 1}: {len(response.data)} soal")
        import time

        time.sleep(0.5)  # Delay untuk menghindari rate limit

    print(f"\n[OK] Berhasil upload {total_uploaded} soal!")

except Exception as e:
    print(f"[ERROR] Upload gagal: {e}")
    import traceback

    traceback.print_exc()

# ========== 4. SIMPAN LAPORAN ==========
print("\n[4] Menyimpan laporan...")
output_dir = Path("../langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_upload_final.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "total_soal": len(db_data),
            "total_uploaded": total_uploaded if "total_uploaded" in locals() else 0,
            "status": "sukses"
            if "total_uploaded" in locals() and total_uploaded > 0
            else "gagal",
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"[OK] Laporan: {laporan_path}")
print("\n=== SELESAI ===")
