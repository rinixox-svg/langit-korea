#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk upload 300 soal ke Supabase:
1. Ekstrak MP3 dari ZIP
2. Match audio ke soal listening
3. Upload ke Supabase dengan UPSERT (hindari duplikat)
"""

import json
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

print("=== UPLOAD SOAL KE SUPABASE ===\n")

base_dir = Path("../assets/langit-korea-extracted")
zip_path = Path("../assets/EPS-TOPIK_textbook2_listen.zip")
supabase_url = "https://YOUR_PROJECT.supabase.co"  # GANTI DENGAN MILIKMU
supabase_key = "YOUR_ANON_KEY"  # GANTI DENGAN MILIKMU

# Cek apakah supabase-py terinstall
try:
    from supabase import Client, create_client

    print("✓ supabase-py terinstall")
except ImportError:
    print("✗ supabase-py belum terinstall. Install dengan: pip install supabase")
    exit(1)

# Inisialisasi Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# 1. Ekstrak MP3 dari ZIP
print("\n=== EKSTRAKSI MP3 DARI ZIP ===")
mp3_dir = Path("./temp_mp3")
mp3_dir.mkdir(parents=True, exist_ok=True)

try:
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Filter hanya file MP3
        mp3_files = [f for f in zip_ref.namelist() if f.endswith(".mp3")]
        print(f"✓ Ditemukan {len(mp3_files)} file MP3")

        # Ekstrak ke temp directory
        for mp3_file in mp3_files:
            # Extract
            zip_ref.extract(mp3_file, mp3_dir)

        print(f"✓ MP3 diekstrak ke: {mp3_dir}")
except Exception as e:
    print(f"✗ Error ekstrak ZIP: {e}")
    exit(1)

# 2. Mapping MP3 ke unit & nomor soal
print("\n=== MAPPING MP3 KE SOAL ===")


def parse_mp3_filename(filename):
    """
    Parse nama file MP3 untuk dapat unit & nomor soal
    Contoh: "Track 178 31 1.mp3" -> unit=31, nomor=1
    """
    # Cari pola: angka angka.mp3
    match = re.search(r"(\d+)\s+(\d+)\.mp3", filename)
    if match:
        # Biasanya: Track XXX unit nomor.mp3
        # Atau: unit nomor.mp3
        parts = Path(filename).stem.split()
        # Cari 2 angka berturut-turut
        numbers = [int(s) for s in parts if s.isdigit()]
        if len(numbers) >= 2:
            # Asumsi: angka terakhir = nomor soal
            # angka sebelum terakhir = unit
            nomor = numbers[-1]
            unit = numbers[-2]
            if 31 <= unit <= 60:
                return unit, nomor
    return None, None


# Buat dictionary mapping: (unit, nomor) -> path MP3
mp3_mapping = {}
for mp3_file in mp3_dir.glob("**/*.mp3"):
    unit, nomor = parse_mp3_filename(mp3_file.name)
    if unit and nomor:
        mp3_mapping[(unit, nomor)] = mp3_file

print(f"✓ Berhasil mapping {len(mp3_mapping)} file MP3")

# 3. Kumpulkan semua soal dari JSON files
print("\n=== MENGUMPULKAN SOAL DARI JSON ===")

all_soal = []

for unit_num in range(31, 61):
    unit_key = f"unit_{unit_num:02d}"
    unit_dir = base_dir / unit_key

    if not unit_dir.exists():
        continue

    # Reading soal
    reading_path = unit_dir / "reading_data.json"
    if reading_path.exists():
        try:
            with open(reading_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            reading_soal = data.get("soal", [])

            for soal in reading_soal:
                soal["bab"] = unit_num
                soal["tipe"] = "membaca"
                soal["sumber_url"] = f"unit_{unit_num:02d}_reading"
                all_soal.append(soal)
        except Exception as e:
            print(f"✗ Error baca {reading_path}: {e}")

    # Listening soal
    listening_path = unit_dir / "listening_data.json"
    if listening_path.exists():
        try:
            with open(listening_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            listening_soal = data.get("soal", [])

            for soal in listening_soal:
                soal["bab"] = unit_num
                soal["tipe"] = "mendengarkan"
                soal["sumber_url"] = f"unit_{unit_num:02d}_listening"

                # Cari MP3 yang sesuai
                mp3_key = (unit_num, soal["nomor"])
                if mp3_key in mp3_mapping:
                    soal["mp3_path"] = mp3_mapping[mp3_key]

                all_soal.append(soal)
        except Exception as e:
            print(f"✗ Error baca {listening_path}: {e}")

print(f"✓ Total soal dikumpulkan: {len(all_soal)}")

# 4. Upload MP3 ke Supabase Storage (jika perlu)
print("\n=== UPLOAD MP3 KE SUPABASE STORAGE ===")

storage_bucket = "audio-mp3"  # Nama bucket di Supabase


def upload_mp3_to_storage(mp3_path, unit_num, nomor):
    """Upload MP3 ke Supabase Storage dan kembalikan public URL"""
    try:
        # Baca file MP3
        with open(mp3_path, "rb") as f:
            mp3_data = f.read()

        # Nama file di storage: unit_{unit}_listening_{nomor}.mp3
        storage_path = f"unit_{unit_num:02d}/listening_{nomor}.mp3"

        # Upload ke Supabase Storage
        response = supabase.storage.from_(storage_bucket).upload(
            storage_path, mp3_data, {"content-type": "audio/mpeg"}
        )

        # Dapatkan public URL
        public_url = supabase.storage.from_(storage_bucket).get_public_url(storage_path)
        return public_url
    except Exception as e:
        print(f"  ✗ Error upload MP3 unit {unit_num} soal {nomor}: {e}")
        return None


# Upload MP3 untuk listening soal
uploaded_audio = 0
for soal in all_soal:
    if soal.get("tipe") == "mendengarkan" and soal.get("mp3_path"):
        mp3_path = soal["mp3_path"]
        unit_num = soal["bab"]
        nomor = soal["nomor"]

        # Cek apakah sudah diupload (bisa cek dari storage atau skip)
        # Untuk sederhana, kita upload semua
        audio_url = upload_mp3_to_storage(mp3_path, unit_num, nomor)

        if audio_url:
            soal["audio_url"] = audio_url
            uploaded_audio += 1
            print(f"  ✓ Unit {unit_num:02d} Soal {nomor}: {audio_url}")
        else:
            soal["audio_url"] = ""

# Hapus temp directory
shutil.rmtree(mp3_dir, ignore_errors=True)

print(f"\n✓ Total MP3 diupload: {uploaded_audio}")

# 5. Siapkan data untuk Supabase
print("\n=== MENYIAPKAN DATA UNTUK SUPABASE ===")

supabase_data = []
for soal in all_soal:
    # Generate ID unik: u{unit}_{tipe}{nomor}
    tipe_prefix = "m" if soal["tipe"] == "membaca" else "l"
    soal_id = f"u{soal['bab']}_{tipe_prefix}{soal['nomor']}"

    # Map jawaban ke jawaban_benar
    jawaban = soal.get("jawaban", "")
    if jawaban in ["a", "b", "c", "d"]:
        jawaban_benar = jawaban
    else:
        jawaban_benar = None

    # Tentukan tingkat (default: sedang)
    tingkat = soal.get("tingkat", "sedang")

    # Tentukan akses (default: free untuk bab 1-18, premium untuk lainnya)
    akses = "free" if soal["bab"] <= 18 else "premium"

    # Gambar URL (jika ada)
    gambar_url = ""
    if soal.get("ada_gambar_pilihan") and soal.get("gambar_pilihan"):
        # Bisa berupa JSON string atau dict
        gambar_url = json.dumps(soal["gambar_pilihan"])

    supabase_row = {
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
        "penjelasan": soal.get("penjelasan", ""),  # Masih kosong
        "tingkat": tingkat,
        "akses": akses,
        "sumber_url": soal.get("sumber_url", ""),
    }

    supabase_data.append(supabase_row)

print(f"✓ Data siap upload: {len(supabase_data)} baris")

# 6. Upload ke Supabase dengan UPSERT
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

# Save laporan
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_upload_supabase.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "total_soal": len(supabase_data),
            "uploaded_audio": uploaded_audio,
            "contoh_data": supabase_data[:2] if supabase_data else {},
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
print("Soal sudah diupload ke Supabase tanpa duplikat!")
print("Langkah selanjutnya: Buat frontend untuk menampilkan soal")
