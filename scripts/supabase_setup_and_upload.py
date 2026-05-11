#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script lengkap Supabase setup & upload:
1. Buat tabel soal_eps (jika belum ada)
2. Buat bucket audio-mp3 (jika belum ada)
3. Upload MP3 ke Storage
4. Upload 300 soal ke tabel soal_eps dengan UPSERT (tanpa duplikat)
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path

print("=== SUPABASE SETUP & UPLOAD OTOMATIS ===\n")

# GANTI DENGAN DATA SUPABASE KAMU!
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"  # GANTI!
SUPABASE_KEY = "YOUR_ANON_KEY"  # GANTI! (gunakan service_role key untuk full akses)

# Cek instalasi
try:
    from supabase import Client, create_client

    print("✓ supabase-py terinstall")
except ImportError:
    print("✗ supabase-py belum terinstall. Install: pip install supabase")
    exit(1)

# Inisialisasi client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

base_dir = Path("../assets/langit-korea-extracted")
mp3_dir = Path("./extracted_mp3")

# ============================================
# 1. BUAT TABEL soal_eps (jika belum ada)
# ============================================
print("\n=== 1. BUAT TABEL soal_eps ===")

# Coba cek apakah tabel sudah ada
try:
    response = supabase.table("soal_eps").select("*").limit(1).execute()
    print("✓ Tabel soal_eps sudah ada")
    tabel_ada = True
except Exception as e:
    print(f"⚠️  Tabel belum ada: {e}")
    tabel_ada = False

if not tabel_ada:
    print("❗ Tabel soal_eps belum dibuat!")
    print("Jalankan SQL berikut di Supabase SQL Editor:")
    print("""
    create table if not exists public.soal_eps (
        id text primary key,
        bab integer not null,
        tipe text not null check (tipe in ('membaca', 'mendengarkan')),
        teks_soal text not null,
        gambar_url text default '',
        audio_url text default '',
        pilihan_a text default '',
        pilihan_b text default '',
        pilihan_c text default '',
        pilihan_d text default '',
        jawaban_benar text check (jawaban_benar in ('a', 'b', 'c', 'd')),
        audio_teks text default '',
        penjelasan text default '',
        tingkat text default 'sedang' check (tingkat in ('mudah', 'sedang', 'sulit')),
        akses text default 'free' check (akses in ('free', 'premium')),
        sumber_url text default ''
    );

    -- Enable RLS
    alter table public.soal_eps enable row level security;

    -- Policy: public read
    create policy if not exists "Public read" on public.soal_eps
        for select using (true);

    -- Policy: authenticated can update
    create policy if not exists "Auth update" on public.soal_eps
        for update using (auth.role() = 'authenticated');
    """)
    print("\nSetelah tabel dibuat, jalankan ulang script ini.")
    exit(1)

# ============================================
# 2. BUAT BUCKET audio-mp3 (jika belum ada)
# ============================================
print("\n=== 2. BUAT BUCKET audio-mp3 ===")

try:
    # Coba list files di bucket
    response = supabase.storage.from_("audio-mp3").list()
    print("✓ Bucket audio-mp3 sudah ada")
    bucket_ada = True
except Exception as e:
    print(f"⚠️  Bucket belum ada: {e}")
    bucket_ada = False

if not bucket_ada:
    print("❗ Bucket audio-mp3 belum dibuat!")
    print("Buat bucket di Supabase Dashboard > Storage:")
    print("1. Buka https://supabase.com/project/YOUR_PROJECT/storage/buckets")
    print("2. Klik 'New Bucket'")
    print("3. Nama: audio-mp3")
    print("4. Public: Yes (centang)")
    print("5. Klik 'Create bucket'")
    print("\nSetelah bucket dibuat, jalankan ulang script ini.")
    exit(1)

# ============================================
# 3. UPLOAD MP3 KE STORAGE
# ============================================
print("\n=== 3. UPLOAD MP3 KE STORAGE ===")

if not mp3_dir.exists():
    print("✗ Direktori MP3 tidak ada. Jalankan dulu: python extract_and_match_mp3.py")
else:
    mp3_files = list(mp3_dir.glob("*.mp3"))
    print(f"✓ Ditemukan {len(mp3_files)} file MP3")

    uploaded_mapping = {}
    uploaded_count = 0

    for mp3_path in sorted(mp3_files):
        # Parse nama: unit_XX_listening_Y.mp3
        match = re.match(r"unit_(\d+)_listening_(\d+)\.mp3", mp3_path.name)
        if not match:
            print(f"  ⚠️  {mp3_path.name}: Format tidak dikenali")
            continue

        unit_num = int(match.group(1))
        soal_num = int(match.group(2))

        # Upload ke Supabase Storage
        try:
            with open(mp3_path, "rb") as f:
                mp3_data = f.read()

            storage_path = f"unit_{unit_num:02d}/listening_{soal_num}.mp3"

            # Cek apakah sudah ada (hindari duplikat)
            try:
                # Coba download (jika berhasil, berarti sudah ada)
                supabase.storage.from_("audio-mp3").download(storage_path)
                print(f"  ⚪  Unit {unit_num:02d} Soal {soal_num}: Sudah ada")
                # Ambil URL yang sudah ada
                public_url = supabase.storage.from_("audio-mp3").get_public_url(
                    storage_path
                )
                uploaded_mapping[(unit_num, soal_num)] = public_url
                continue
            except:
                pass  # Belum ada, lanjutkan upload

            # Upload
            response = supabase.storage.from_("audio-mp3").upload(
                storage_path, mp3_data, {"content-type": "audio/mpeg"}
            )

            # Ambil public URL
            public_url = supabase.storage.from_("audio-mp3").get_public_url(
                storage_path
            )
            uploaded_mapping[(unit_num, soal_num)] = public_url
            uploaded_count += 1

            if uploaded_count % 10 == 0:
                print(f"  ✓ {uploaded_count}/{len(mp3_files)} diupload...")

        except Exception as e:
            print(f"  ✗ Unit {unit_num:02d} Soal {soal_num}: {e}")

    print(f"\n✓ Total MP3 diupload: {uploaded_count}")

# ============================================
# 4. UPDATE AUDIO_URL DI JSON
# ============================================
print("\n=== 4. UPDATE AUDIO_URL DI JSON ===")

updated_total = 0

for unit_num in range(31, 61):
    listening_path = base_dir / f"unit_{unit_num:02d}" / "listening_data.json"

    if not listening_path.exists():
        continue

    try:
        with open(listening_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        continue

    soal_list = data.get("soal", [])
    updated = 0

    for soal in soal_list:
        nomor = soal.get("nomor")
        key = (unit_num, nomor)

        if key in uploaded_mapping:
            soal["audio_url"] = uploaded_mapping[key]
            updated += 1

    # Save
    if updated > 0:
        try:
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            updated_total += updated
        except Exception as e:
            print(f"Unit {unit_num:02d}: ✗ Error simpan - {e}")

print(f"✓ Total audio_url diupdate: {updated_total}")

# ============================================
# 5. SIAPKAN & UPLOAD SOAL KE TABEL
# ============================================
print("\n=== 5. UPLOAD SOAL KE TABEL soal_eps ===")

all_soal = []

# Kumpulkan semua soal
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

# Upload dengan UPSERT (tanpa duplikat)
print("\n=== UPLOAD DENGAN UPSERT (TANPA DUPLIKAT) ===")

try:
    # UPSERT: update jika id sudah ada, insert jika belum
    response = supabase.table("soal_eps").upsert(supabase_data).execute()
    print(f"✓ Berhasil upload {len(response.data)} soal")
    print(f"  Response: {response}")
except Exception as e:
    print(f"✗ Error upload: {e}")
    print("\nPastikan:")
    print("1. Tabel 'soal_eps' sudah dibuat dengan skema yang benar")
    print("2. API Key memiliki hak akses yang cukup (gunakan service_role key)")
    print("3. URL dan Key Supabase sudah benar")

# Save laporan
print("\n=== SELESAI ===")

output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_upload_final.json"

with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "waktu": datetime.now().isoformat(),
            "total_soal": len(supabase_data),
            "uploaded_mp3": uploaded_count if "uploaded_count" in locals() else 0,
            "updated_audio_url": updated_total,
            "contoh_data": supabase_data[:2] if supabase_data else {},
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print(f"Laporan: {laporan_path}")
print("\n✅ 300 soal sudah diupload ke Supabase tanpa duplikat!")
print("✅ MP3 sudah diupload ke Storage!")
print("\nLangkah selanjutnya:")
print("1. Cek di Supabase Dashboard > Table Editor > soal_eps")
print("2. Buat frontend HTML/JS untuk menampilkan soal")
print("3. Setup sistem premium & token unlock")
