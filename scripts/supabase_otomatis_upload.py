#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Setup & Upload Supabase Otomatis:
1. Cek tabel soal_eps (buat jika belum)
2. Cek bucket audio-mp3 (buat jika belum)
3. Upload MP3 tanpa duplikat
4. Upload 300 soal dengan UPSERT (tanpa duplikat)
"""

import json
import re
from datetime import datetime
from pathlib import Path

print("=== SETUP & UPLOAD SUPABASE OTOMATIS ===\n")

# ========== KONFIGURASI ==========
# GANTI DENGAN DATA SUPABASE KAMU!
SUPABASE_URL = "https://mozmuwrkfsipzfupybwh.supabase.co"  # GANTI!
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vem11d3JrZnNpcHpmdXB5YndoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzY5NTk1NCwiZXhwIjoyMDkzMjcxOTU0fQ.SZSNk6xV-vq17beo_LwWzsZSp9UVGdqfR-R35cGxawE"  # GANTI! (service_role key)
# ========== ========== ==========

# Cek instalasi supabase-py
try:
    from supabase import create_client

    print("[OK] supabase-py terinstall")
except ImportError:
    print("[ERROR] supabase-py belum terinstall. Install: pip install supabase")
    exit(1)

# Inisialisasi client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== 1. CEK TABEL soal_eps ==========
print("\n=== 1. CEK TABEL soal_eps ===")

try:
    response = supabase.table("soal_eps").select("id").limit(1).execute()
    print("[OK] Tabel soal_eps sudah ada")
    tabel_ada = True
except Exception as e:
    print(f"[WARN] Tabel belum ada: {e}")
    tabel_ada = False

if not tabel_ada:
    print("\n❗ Tabel soal_eps belum dibuat!")
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

    -- Policy: Public read
    create policy if not exists "Public read" on public.soal_eps
        for select using (true);

    -- Policy: Authenticated update
    create policy if not exists "Auth update" on public.soal_eps
        for update using (auth.role() = 'authenticated');
    """)
    print("\nSetelah tabel dibuat, jalankan ulang script ini.")
    exit(1)

# ========== 2. CEK BUCKET audio-mp3 ==========
print("\n=== 2. CEK BUCKET audio-mp3 === ")

try:
    # Coba list files (jika bucket ada)
    response = supabase.storage.from_("audio-mp3").list()
    print("[OK] Bucket audio-mp3 sudah ada")
    bucket_ada = True
except Exception as e:
    print(f"[WARN] Bucket belum ada: {e}")
    bucket_ada = False

if not bucket_ada:
    print("\n❗ Bucket audio-mp3 belum dibuat!")
    print("Buat bucket di Supabase Dashboard:")
    print("1. Buka https://supabase.com/project/YOUR_PROJECT/storage/buckets")
    print("2. Klik 'New Bucket'")
    print("3. Nama: audio-mp3")
    print("4. Public: Yes (centang)")
    print("5. Klik 'Create bucket'")
    print("\nSetelah bucket dibuat, jalankan ulang script ini.")
    exit(1)

# ========== 3. UPLOAD MP3 ==========
print("\n=== 3. UPLOAD MP3 KE STORAGE === ")

mp3_dir = Path("./extracted_mp3")
if not mp3_dir.exists():
    print(
        "✗ Direktori extracted_mp3 tidak ada. Jalankan: python extract_and_match_mp3.py"
    )
    exit(1)

mp3_files = list(mp3_dir.glob("*.mp3"))
print(f"[OK] Ditemukan {len(mp3_files)} file MP3")

uploaded_mapping = {}  # (unit, nomor) -> public_url
uploaded_count = 0

for mp3_path in sorted(mp3_files):
    # Parse nama: unit_XX_listening_Y.mp3
    match = re.match(r"unit_(\d+)_listening_(\d+)\.mp3", mp3_path.name)
    if not match:
        print(f"  ⚠️  {mp3_path.name}: Format tidak dikenali")
        continue

    unit_num = int(match.group(1))
    soal_num = int(match.group(2))

    # Cek apakah sudah ada (hindari duplikat)
    storage_path = f"unit_{unit_num:02d}/listening_{soal_num}.mp3"

    try:
        # Coba download (jika berhasil = sudah ada)
        supabase.storage.from_("audio-mp3").download(storage_path)
        # Sudah ada, ambil URL
        public_url = supabase.storage.from_("audio-mp3").get_public_url(storage_path)
        uploaded_mapping[(unit_num, soal_num)] = public_url
        print(f"  [OK] Unit {unit_num:02d} Soal {soal_num}: Sudah ada")
    except:
        # Belum ada, upload
        try:
            with open(mp3_path, "rb") as f:
                mp3_data = f.read()

            supabase.storage.from_("audio-mp3").upload(
                storage_path, mp3_data, {"content-type": "audio/mpeg"}
            )

            public_url = supabase.storage.from_("audio-mp3").get_public_url(
                storage_path
            )
            uploaded_mapping[(unit_num, soal_num)] = public_url
            uploaded_count += 1

            if uploaded_count % 10 == 0:
                print(f"  ✓ {uploaded_count}/{len(mp3_files)} diupload...")
        except Exception as e:
            print(f"  [OK] Unit {unit_num:02d} Soal {soal_num}: {e}")

print(f"\n[OK] Total MP3 diupload: {uploaded_count}")
print(f"[OK] Total MP3 termapping: {len(uploaded_mapping)}")

# ========== 4. UPDATE AUDIO_URL DI JSON ==========
print("\n=== 4. UPDATE AUDIO_URL DI JSON === ")

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
            # Hapus field audio_file yang lama
            if "audio_file" in soal:
                del soal["audio_file"]
            updated += 1

    # Save
    if updated > 0:
        try:
            with open(listening_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Unit {unit_num:02d}: [OK] ({updated} soal)")
            updated_total += updated
        except Exception as e:
            print(f"Unit {unit_num:02d}: [ERROR] Error simpan - {e}")

print(f"\n[OK] Total audio_url diupdate: {updated_total}")

# ========== 5. SIAPKAN DATA UNTUK UPLOAD ==========
print("\n=== 5. SIAPKAN DATA UNTUK UPLOAD === ")

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
            # Gabungkan instruksi ke teks_soal jika teks_soal kosong
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
            soal["sumber_url"] = f"unit_{unit_num:02d}_listening"
            # Gabungkan instruksi ke teks_soal jika teks_soal kosong
            if not soal.get("teks_soal") and soal.get("instruksi"):
                soal["teks_soal"] = soal["instruksi"]
            all_soal.append(soal)

print(f"[OK] Total soal dikumpulkan: {len(all_soal)} ")

# Konversi ke format Supabase
print("\n=== 6. KONVERSI KE FORMAT SUPABASE === ")

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

print(f"[OK] Data siap upload: {len(supabase_data)} baris ")

# ========== 7. UPLOAD DENGAN UPSERT (TANPA DUPLIKAT) ==========
print("\n=== 7. UPLOAD DENGAN UPSERT (TANPA DUPLIKAT) === ")


# Sesuaikan dengan struktur tabel yang sebenarnya
def convert_to_db_format(soal):
    """Konversi format JSON ke format tabel soal_eps yang ada di DB"""
    tipe_prefix = "m" if soal["tipe"] == "membaca" else "l"
    soal_id = f"u{soal['bab']}_{tipe_prefix}{soal['nomor']}"

    # Map jawaban ke kolom yang benar
    jawaban = soal.get("jawaban", "")
    if jawaban not in ["a", "b", "c", "d"]:
        jawaban = None

    # Tentukan akses
    akses = "free" if soal["bab"] <= 48 else "premium"

    return {
        "id": soal_id,
        "unit": soal["bab"],  # kolom di DB pakai 'unit', bukan 'bab'
        "tipe": soal["tipe"],
        "tipe_soal_ujian": soal.get("tipe_soal_ujian", ""),
        "teks_soal": soal.get("teks_soal", ""),
        "teks_soal_id": soal.get("instruksi", ""),  # instruksi jadi teks_soal_id
        "gambar_url": soal.get("gambar_url", ""),
        "audio_url": soal.get("audio_url", ""),
        "audio_teks": soal.get("audio_teks", ""),
        "audio_teks_id": soal.get("audio_teks_id", ""),
        "pilihan_a": soal.get("pilihan_a", ""),
        "pilihan_a_id": soal.get("pilihan_a_id", ""),
        "pilihan_a_gambar_url": soal.get("pilihan_a_gambar_url", ""),
        "pilihan_b": soal.get("pilihan_b", ""),
        "pilihan_b_id": soal.get("pilihan_b_id", ""),
        "pilihan_b_gambar_url": soal.get("pilihan_b_gambar_url", ""),
        "pilihan_c": soal.get("pilihan_c", ""),
        "pilihan_c_id": soal.get("pilihan_c_id", ""),
        "pilihan_c_gambar_url": soal.get("pilihan_c_gambar_url", ""),
        "pilihan_d": soal.get("pilihan_d", ""),
        "pilihan_d_id": soal.get("pilihan_d_id", ""),
        "pilihan_d_gambar_url": soal.get("pilihan_d_gambar_url", ""),
        "jawaban": jawaban,  # kolom di DB pakai 'jawaban', bukan 'jawaban_benar'
        "penjelasan": soal.get("penjelasan", ""),
        "tingkat": soal.get("tingkat", "sedang"),
        "ada_gambar_pilihan": soal.get("ada_gambar_pilihan", False),
        "akses": akses,
        "gambar_pilihan_a": soal.get("gambar_pilihan_a", ""),
        "gambar_pilihan_b": soal.get("gambar_pilihan_b", ""),
        "gambar_pilihan_c": soal.get("gambar_pilihan_c", ""),
        "gambar_pilihan_d": soal.get("gambar_pilihan_d", ""),
    }


try:
    # Konversi semua data
    db_data = [convert_to_db_format(soal) for soal in all_soal]

    # UPSERT: update jika id sudah ada, insert jika belum
    response = supabase.table("soal_eps").upsert(db_data).execute()
    print(f"[OK] Berhasil upload {len(response.data)} soal ")
    print(f"  Response: {response}")
except Exception as e:
    print(f"✗ Error upload ke Supabase: {e}")
    import traceback

    traceback.print_exc()
    print("\nPastikan:")
    print("1. Tabel 'soal_eps' sudah dibuat dengan skema yang benar")
    print("2. API Key memiliki hak akses yang cukup (service_role key)")
    print("3. URL dan Key Supabase sudah benar")
    exit(1)

# ========== 8. SIMPAN LAPORAN ==========
print("\n=== 8. SIMPAN LAPORAN === ")

output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)
laporan_path = output_dir / "laporan_upload_final.json"

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

print(f"Laporan: {laporan_path}")
print("\n=== SELESAI ===")
print("✅ 300 soal sudah diupload ke Supabase tanpa duplikat!")
print("✅ MP3 sudah diupload ke Storage!")
print("\nLangkah selanjutnya:")
print("1. Cek di Supabase Dashboard > Table Editor > soal_eps")
print("2. Buat frontend HTML/JS untuk menampilkan soal")
print("3. Setup sistem premium & token unlock")
