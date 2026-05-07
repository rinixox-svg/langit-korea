#!/usr/bin/env python3
import os

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # Coba baca ANON key
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Coba baca SERVICE key

print(f"URL: {SUPABASE_URL}")
print(f"ANON Key (first 20 chars): {(SUPABASE_ANON_KEY or '')[:20]}...")
print(f"SERVICE Key (first 20 chars): {(SUPABASE_SERVICE_KEY or '')[:20]}...")

# Coba koneksi
try:
    from supabase import create_client

    # Coba pakai ANON key dulu
    if SUPABASE_ANON_KEY:
        print("\nMencoba koneksi dengan ANON key...")
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        # Test query sederhana
        result = client.table("soal_eps").select("*").limit(1).execute()
        print("✅ Koneksi dengan ANON key BERHASIL!")
    elif SUPABASE_SERVICE_KEY:
        print("\nMencoba koneksi dengan SERVICE ROLE key...")
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        result = client.table("soal_eps").select("*").limit(1).execute()
        print("✅ Koneksi dengan SERVICE ROLE key BERHASIL!")
    else:
        print("\n❌ Tidak ada key yang ditemukan di .env")
        print("Pastikan ada SUPABASE_ANON_KEY atau SUPABASE_SERVICE_KEY")

except Exception as e:
    print(f"\n❌ Koneksi GAGAL: {e}")
    print("\nKemungkinan penyebab:")
    print("1. Key yang diisikan salah/tidak valid")
    print("2. URL Supabase salah")
    print("3. Key sudah expired (coba regenerate di Dashboard)")
