#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload MP3 ke Supabase Storage dan update audio_url:
1. Upload MP3 dari extracted_mp3/ ke Supabase Storage
2. Update field audio_url di listening_data.json
3. Upload 300 soal ke tabel soal_eps dengan UPSERT
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== UPLOAD KE SUPABASE ===\n")

# GANTI DENGAN MILIKMU!
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"  # GANTI DENGAN MILIKMU
SUPABASE_KEY = "YOUR_ANON_KEY"  # GANTI DENGAN MILIKMU

# Cek apakah supabase-py terinstall
try:
    from supabase import Client, create_client

    print("✓ supabase-py terinstall")
except ImportError:
    print("✗ supabase-py belum terinstall. Install dengan: pip install supabase")
    exit(1)

# Inisialisasi Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Upload MP3 ke Supabase Storage
print("\n=== UPLOAD MP3 KE SUPABASE STORAGE ===")

mp3_dir = Path("./extracted_mp3")
storage_bucket = "audio-mp3"  # Nama bucket di Supabase

if not mp3_dir.exists():
    print(f"✗ Direktori {mp3_dir} tidak ada")
    print("   Jalankan dulu: python extract_and_match_mp3.py")
    exit(1)

mp3_files = list(mp3_dir.glob("*.mp3"))
print(f"✓ Ditemukan {len(mp3_files)} file MP3")

uploaded_count = 0
uploaded_mapping = {}  # (unit, nomor) -> public_url

for mp3_path in sorted(mp3_files):
    # Parse nama file: unit_XX_listening_Y.mp3
    match = re.match(r"unit_(\d+)_listening_(\d+)\.mp3", mp3_path.name)
    if not match:
        print(f"  ⚠️  {mp3_path.name}: Format nama tidak dikenali")
        continue

    unit_num = int(match.group(1))
    soal_num = int(match.group(2))

    # Upload ke Supabase Storage
    try:
        # Baca file MP3
        with open(mp3_path, "rb") as f:
            mp3_data = f.read()

        # Nama file di storage: unit_XX/listening_Y.mp3
        storage_path = f"unit_{unit_num:02d}/listening_{soal_num}.mp3"

        # Upload
        response = supabase.storage.from_(storage_bucket).upload(
            storage_path, mp3_data, {"content-type": "audio/mpeg"}
        )

        # Dapatkan public URL
        public_url = supabase.storage.from_(storage_bucket).get_public_url(storage_path)

        uploaded_mapping[(unit_num, soal_num)] = public_url
        uploaded_count += 1

        if uploaded_count % 10 == 0:
            print(f"  ✓ {uploaded_count}/{len(mp3_files)} diupload...")

    except Exception as e:
        print(f"  ✗ {mp3_path.name}: {e}")

print(f"\n✓ Total MP3 diupload: {uploaded_count}")

# 2. Update listening_data.json dengan audio_url
print("\n=== UPDATE AUDIO_URL DI LISTENING_DATA ===")

base_dir = Path("../assets/langit-korea-extracted")
updated_total = 0

for unit_num in range(31, 61):
    listening_path = base_dir / f"unit_{unit_num:02d}" / "listening_data.json"

    if not listening_path.exists():
        continue

    try:
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Unit {unit_num:02d}: ✗ Error baca - {e}")
        continue

    soal_list = data.get("soal", [])
    updated = 0

    for soal in soal_list:
        nomor = soal.get("nomor")
        key = (unit_num, nomor)

        if key in uploaded_mapping:
            soal["audio_url"] = uploaded_mapping[key]
            # Hapus audio_file yang lama
            if "audio_file" in soal:
                del soal["audio_file"]
            updated += 1

    # Save
    if updated > 0:
        try:
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Unit {unit_num:02d}: ✓ ({updated} soal)")
            updated_total += updated
        except Exception as e:
            print(f"Unit {unit_num:02d}: ✗ Error simpan - {e}")

print(f"\n✓ Total audio_url diupdate: {updated_total}")

# 3. Siapkan data untuk upload ke tabel soal_eps
print("\n=== SIAPKAN DATA UNTUK SUPABASE ===")

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
            soal["sumber_url"] = f"unit_{unit_num:02d}_reading"
            all_soal.append(soal)

    # Listening
    listening_path = unit_dir / "listening_data.json"
    if listening_path.exists():
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for soal in data.get("soal", []):
            soal["bab"] = unit_num
            soal["tipe"] = "mendengarkan"
            soal["sumber_url"] = f"unit_{unit_num:02d}_listening"
            all_soal.append(soal)

print(f"✓ Total soal dikumpulkan: {len(all_soal)}")

# Konversi ke format Supabase
print("\n=== KONVERSI KE FORMAT SUPABASE ===")

supabase_data = []

for soal in all_soal:
    # Generate ID
    tipe_prefix = "m" if soal["tipe"] == "membaca" else "l"
    soal_id = f"u{soal['bab']}_{tipe_prefix}{soal['nomor']}"

    # Jawaban benar
    jawaban = soal.get("jawaban", "")
    jawaban_benar = jawaban if jawaban in ["a", "b", "c", "d"] else None

    # Tingkat
    tingkat = soal.get("tingkat", "sedang")

    # Akses
    akses = "free" if soal["bab"] <= 18 else "premium"

    # Gambar URL
    gambar_url = ""
    if soal.get("ada_gambar_pilihan") and soal.get("gambar_pilihan"):
        gambar_url = json.dumps(soal["gambar_pilihan"])

    row = {
        "id": soal_id,
        "bab": soal["bab"],
        "tipe": soal["tipe"],
        "teks_soal": soal.get("teks_soal", ""),
        "gambar_url": gambar_url,
        "audio_url": soal.get("audio_url", ""),
        "pilihan_a": soal.get("pilihan_a", ""),
        "pilihan_b": soal.get("pilihan_b", ""),
        "pilihan_c": soal.get("pilihan_c", ""),
        "pilihan_d": soal.get("pilihan_d", ""),
        "jawaban_benar": jawaban_benar,
        "audio_teks": soal.get("audio_teks", ""),
        "penjelasan": soal.get("penjelasan", ""),
        "tingkat": tingkat,
        "akses": akses,
        "sumber_url": soal.get("sumber_url", ""),
    }

    supabase_data.append(row)

print(f"✓ Data siap upload: {len(supabase_data)} baris")

# 4. Upload ke Supabase dengan UPSERT
print("\n=== UPLOAD KE SUPABASE (UPSERT) ===")

try:
    # UPSERT: update jika id sudah ada, insert jika belum
    response = supabase.table("soal_eps").upsert(supabase_data).execute()
    print(f"✓ Berhasil upload {len(response.data)} soal")
    print(f"  Response: {response}")
except Exception as e:
    print(f"✗ Error upload ke Supabase: {e}")
    print("\nPastikan:")
    print("1. Tabel 'soal_eps' sudah dibuat dengan skema yang benar")
    print("2. API Key memiliki hak akses yang cukup (service_role key)")
    print("3. URL dan Key Supabase sudah benar")
    print("4. Bucket 'audio-mp3' sudah dibuat di Supabase Storage")

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_upload_supabase_final.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "total_soal": len(supabase_data),
            "uploaded_mp3": uploaded_count,
            "updated_audio_url": updated_total,
            "contoh_data": supabase_data[:2] if supabase_data else {},
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
print("✅ 300 soal sudah diupload ke Supabase!")
print("✅ MP3 sudah di Supabase Storage!")
print("\nLangkah selanjutnya:")
print("1. Buat frontend HTML/JS untuk menampilkan soal")
print("2. Setup sistem premium & token unlock")
