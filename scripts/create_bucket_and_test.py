#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk:
1. Test koneksi Supabase
2. Membuat storage bucket 'audio-mp3' jika belum ada
3. Verifikasi tabel soal_eps
"""

from datetime import datetime

from supabase import create_client

print("=== TEST KONEKSI & SETUP SUPABASE ===\n")

# ========== KONFIGURASI ==========
# GANTI DENGAN DATA SUPABASE KAMU!
SUPABASE_URL = "https://mozmuwrkfsipzfupybwh.supabase.co"  # GANTI!
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vem11d3JrZnNpcHpmdXB5YndoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzY5NTk1NCwiZXhwIjoyMDkzMjcxOTU0fQ.SZSNk6xV-vq17beo_LwWzsZSp9UVGdqfR-R35cGxawE"  # GANTI! (service_role key)
# ========== ========== ==========

# Inisialisasi client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Berhasil koneksi ke Supabase")
except Exception as e:
    print(f"✗ Gagal koneksi: {e}")
    print("\nPastikan URL dan KEY benar!")
    exit(1)

# ========== 1. CEK TABEL soal_eps ==========
print("\n=== 1. CEK TABEL soal_eps ===")

try:
    response = supabase.table("soal_eps").select("id").limit(1).execute()
    print("✓ Tabel soal_eps sudah ada")
    print(f"  Response: {response}")
except Exception as e:
    print(f"✗ Tabel soal_eps belum ada: {e}")
    print("\n❗ Silakan jalankan SQL berikut di Supabase SQL Editor:")
    print("   Buka file: setup_soal_eps_final.sql")
    print("   Copy isi file tersebut, lalu jalankan di SQL Editor")

# ========== 2. BUAT STORAGE BUCKET ==========
print("\n=== 2. CEK / BUAT STORAGE BUCKET ===")

bucket_name = "audio-mp3"

try:
    # Cek apakah bucket sudah ada
    buckets = supabase.storage.list_buckets()
    bucket_exists = any(b.name == bucket_name for b in buckets)

    if bucket_exists:
        print(f"✓ Bucket '{bucket_name}' sudah ada")
    else:
        print(f"⚠️  Bucket '{bucket_name}' belum ada, mencoba membuat...")
        try:
            supabase.storage.create_bucket(
                bucket_name,
                options={"public": True},  # Set public agar bisa diakses tanpa auth
            )
            print(f"✓ Bucket '{bucket_name}' berhasil dibuat (public)")
        except Exception as create_error:
            print(f"✗ Gagal membuat bucket via API: {create_error}")
            print(f"\n❗ Silakan buat bucket secara manual di Supabase Dashboard:")
            print(f"   1. Buka: {SUPABASE_URL}/storage/buckets")
            print(f"   2. Klik 'New Bucket'")
            print(f"   3. Nama: {bucket_name}")
            print(f"   4. Public: ✅ Centang")
            print(f"   5. Klik 'Create bucket'")

except Exception as e:
    print(f"✗ Error cek bucket: {e}")

# ========== 3. TEST UPLOAD FILE KECIL ==========
print("\n=== 3. TEST UPLOAD FILE (opsional) ===")

try:
    # Buat file test kecil
    test_content = b"test audio url"
    test_path = f"test/connection_test.txt"

    supabase.storage.from_(bucket_name).upload(
        test_path, test_content, {"content-type": "text/plain"}
    )

    # Ambil public URL
    public_url = supabase.storage.from_(bucket_name).get_public_url(test_path)
    print(f"✓ Test upload berhasil!")
    print(f"  URL: {public_url}")

    # Hapus file test
    supabase.storage.from_(bucket_name).remove([test_path])
    print("✓ Test file dihapus")

except Exception as e:
    print(f"⚠️  Test upload gagal (tapi tidak masalah): {e}")
    print("   Pastikan bucket sudah dibuat dan public")

# ========== 4. RINGKASAN ==========
print("\n=== RINGKASAN ===")
print("1. Pastikan tabel 'soal_eps' sudah dibuat (jalankan setup_soal_eps_final.sql)")
print("2. Pastikan bucket 'audio-mp3' sudah dibuat (via Dashboard atau script ini)")
print("3. Jika semua sudah OK, jalankan: python supabase_otomatis_upload.py")

print("\n✅ Test selesai!")
