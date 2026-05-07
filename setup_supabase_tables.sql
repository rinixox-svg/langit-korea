-- SQL Setup untuk Langit Korea Supabase
-- Jalankan di Supabase Dashboard > SQL Editor

-- 1. Tabel materi_unit (konten materi belajar)
CREATE TABLE IF NOT EXISTS public.materi_unit (
  id          SERIAL PRIMARY KEY,
  unit        INTEGER NOT NULL,
  title_ko    TEXT,
  title_id    TEXT,
  kategori    TEXT CHECK (kategori IN ('vocab','grammar','conversation','culture')),
  sub         INTEGER DEFAULT 1,
  teks        TEXT,
  akses       TEXT DEFAULT 'free',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.materi_unit ENABLE ROW LEVEL SECURITY;

-- Policy: Materi free bisa diakses publik
-- Gunakan DO block untuk menangani error jika policy sudah ada
DO $$
BEGIN
  CREATE POLICY "Materi free publik"
    ON public.materi_unit FOR SELECT
    TO anon, authenticated
    USING (akses = 'free');
EXCEPTION WHEN duplicate_object THEN
  NULL; -- Abaikan jika policy sudah ada
END $$;

-- 2. Tabel gambar_materi (gambar vocab/grammar/culture)
CREATE TABLE IF NOT EXISTS public.gambar_materi (
  id          SERIAL PRIMARY KEY,
  unit        INTEGER NOT NULL,
  kategori    TEXT NOT NULL,
  sub         INTEGER DEFAULT 1,
  urutan      INTEGER DEFAULT 1,
  storage_url TEXT NOT NULL,
  lebar       INTEGER,
  tinggi      INTEGER,
  akses       TEXT DEFAULT 'free',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.gambar_materi ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  CREATE POLICY "Gambar materi publik"
    ON public.gambar_materi FOR SELECT
    TO anon, authenticated
    USING (akses = 'free');
EXCEPTION WHEN duplicate_object THEN
  NULL;
END $$;

-- 3. Update tabel soal_eps (tambah kolom gambar pilihan)
ALTER TABLE soal_eps
  ADD COLUMN IF NOT EXISTS gambar_pilihan_a TEXT,
  ADD COLUMN IF NOT EXISTS gambar_pilihan_b TEXT,
  ADD COLUMN IF NOT EXISTS gambar_pilihan_c TEXT,
  ADD COLUMN IF NOT EXISTS gambar_pilihan_d TEXT;

-- Index untuk performa
CREATE INDEX IF NOT EXISTS idx_materi_unit_unit ON materi_unit(unit);
CREATE INDEX IF NOT EXISTS idx_gambar_materi_unit ON gambar_materi(unit);
CREATE INDEX IF NOT EXISTS idx_soal_eps_unit ON soal_eps(unit);

-- 4. Buat storage bucket (jika belum ada)
-- Di Supabase Dashboard: Storage > Create bucket
-- Nama: "gambar-materi" → Public: YES
-- Nama: "gambar-soal"   → Public: YES
