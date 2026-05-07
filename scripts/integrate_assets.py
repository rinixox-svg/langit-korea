#!/usr/bin/env python3
"""
Script untuk mengintegrasikan semua aset ke Supabase:
1. Upload gambar ke Storage (bucket: images)
2. Extract audio ZIP dan upload ke Storage (bucket: audio)
3. Load data JSON ke table soal_eps
4. Convert PDF modules ke JSON (opsional)
"""

import os
import json
import zipfile
import io
from supabase import create_client, Client

# === KONFIGURASI SUPABASE ===
# Baca dari js/supabase-config.js
config_path = 'js/supabase-config.js'
supabase_url = None
supabase_key = None

try:
    with open(config_path, 'r') as f:
        content = f.read()
        # Cari URL
        import re
        url_match = re.search(r'SUPABASE_URL\s*=\s*"([^"]+)"', content)
        key_match = re.search(r'SUPABASE_ANON_KEY\s*=\s*"([^"]+)"', content)

        if url_match and key_match:
            supabase_url = url_match.group(1)
            supabase_key = key_match.group(1)
            print(f"✅ Ditemukan Supabase URL: {supabase_url}")
        else:
            print("❌ Tidak ditemukan kredensial di js/supabase-config.js")
            # Gunakan default
            supabase_url = "https://mozmuwrkfsipzfupybwh.supabase.co"
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1veG11d2tmc2lwemZ1cHlid2giLCJyb2xlIjoicm9sZSIsImlhdCI6MTczNjc2MzU1NH0.RPqu-07AyKygnS_bPhMO_IgXSz2r8jkljPc5TGq7Vzg"
except Exception as e:
    print(f"Error baca config: {e}")
    supabase_url = "https://mozmuwrkfsipzfupybwh.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1veG11d2tmc2lwemZ1cHlid2giLCJyb2xlIjoicm9sZSIsImlhdCI6MTczNjc2MzU1NH0.RPqu-07AyKygnS_bPhMO_IgXSz2r8jkljPc5TGq7Vzg"

print(f"Menggunakan Supabase URL: {supabase_url}")

# Inisialisasi Supabase client
try:
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Supabase client berhasil diinisialisasi")
except Exception as e:
    print(f"❌ Gagal inisialisasi Supabase: {e}")
    exit(1)

# === 1. UPLOAD GAMBAR KE STORAGE ===
print("\n=== MENGUPLOAD GAMBAR KE STORAGE ===")
images_bucket = 'images'
images_dir = 'assets/langit-korea-images'

if os.path.exists(images_dir):
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpeg', '.jpg', '.png'))]
    print(f"Ditemukan {len(image_files)} file gambar")

    for idx, filename in enumerate(image_files):
        filepath = os.path.join(images_dir, filename)
        try:
            with open(filepath, 'rb') as f:
                # Upload ke Supabase Storage
                # Path di bucket: images/filename
                response = supabase.storage.from(images_bucket).upload(
                    filename,  # Path di bucket
                    f.read(),
                    {"content-type": "image/jpeg"}  # Sesuaikan content-type
                )
                if idx % 10 == 0:
                    print(f"  Uploaded {idx+1}/{len(image_files)}: {filename}")
        except Exception as e:
            print(f"  ❌ Gagal upload {filename}: {e}")
    print(f"✅ Selesai upload gambar ({len(image_files)} file)")
else:
    print(f"❌ Direktori {images_dir} tidak ditemukan")

# === 2. EXTRACT AUDIO ZIP DAN UPLOAD KE STORAGE ===
print("\n=== MENGEXTRACT AUDIO DARI ZIP DAN UPLOAD ===")
audio_bucket = 'audio'
zip_files = [
    'assets/EPS-TOPIK_textbook1_listen.zip',
    'assets/EPS-TOPIK_textbook2_listen.zip'
]

for zip_path in zip_files:
    if not os.path.exists(zip_path):
        print(f"❌ File {zip_path} tidak ditemukan, lewati...")
        continue

    print(f"Mengekstrak {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            mp3_files = [f for f in zip_ref.namelist() if f.lower().endswith('.mp3')]
            print(f"  Ditemukan {len(mp3_files)} file MP3")

            for idx, mp3_name in enumerate(mp3_files):
                try:
                    # Baca file dari ZIP
                    mp3_data = zip_ref.read(mp3_name)

                    # Upload ke Supabase Storage
                    # Path: audio/mp3_name
                    response = supabase.storage.from(audio_bucket).upload(
                        mp3_name,
                        mp3_data,
                        {"content-type": "audio/mpeg"}
                    )
                    if idx % 5 == 0:
                        print(f"  Uploaded {idx+1}/{len(mp3_files)}: {mp3_name}")
                except Exception as e:
                    print(f"  ❌ Gagal upload {mp3_name}: {e}")
            print(f"✅ Selesai upload audio dari {zip_path}")
    except Exception as e:
        print(f"❌ Gagal ektrak {zip_path}: {e}")

# === 3. LOAD DATA JSON KE TABLE SOAL_EPS ===
print("\n=== MENGLOAD DATA JSON KE TABLE SOAL_EPS ===")
json_dirs = [
    'assets/langit-korea-extracted',
    'assets/langit-korea-json'  # Jika ada
]

for json_dir in json_dirs:
    if not os.path.exists(json_dir):
        print(f"❌ Direktori {json_dir} tidak ditemukan, lewati...")
        continue

    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    print(f"Ditemukan {len(json_files)} file JSON di {json_dir}")

    for idx, filename in enumerate(json_files):
        filepath = os.path.join(json_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Asumsikan data adalah array of objects
                if isinstance(data, list):
                    for item in data:
                        # Sesuaikan dengan struktur tabel soal_eps
                        # Kolom: id, bab, tipe, teks_soal, gambar_url, audio_url, pilihan_a, dst, jawaban_benar, penjelasan, tingkat, akses
                        try:
                            # Cek apakah sudah ada (berdasarkan id atau bab + no)
                            # Insert ke tabel
                            result = supabase.table('soal_eps').insert(item)
                        except Exception as e:
                            print(f"  ❌ Gagal insert {filename}: {e}")
                elif isinstance(data, dict):
                    # Mungkin strukturnya beda
                    print(f"  File {filename} adalah dict, perlu penyesuaian")
        except Exception as e:
            print(f"  ❌ Gagal baca {filename}: {e}")
    print(f"✅ Selesai load JSON dari {json_dir}")

# === 4. KONVERSI PDF KE JSON (OPSIoNAL) ===
print("\n=== KONVERSI PDF MODULES KE JSON ===")
pdf_dir = 'assets/langit-korea-modules'
if os.path.exists(pdf_dir):
    print(f"Direktori {pdf_dir} ditemukan. Untuk mengkonversi PDF ke JSON, jalankan convert_all.py terlebih dahulu.")
else:
    print(f"❌ Direktori {pdf_dir} tidak ditemukan")

print("\n=== INTEGRASI SELESAI ===")
print("Cek di Supabase Dashboard:")
print("1. Storage → buckets 'images' dan 'audio' untuk file-file yang sudah diupload")
print("2. Table Editor → tabel 'soal_eps' untuk data soal")
print("3. Pastikan RLS (Row Level Security) sudah diatur dengan benar")
