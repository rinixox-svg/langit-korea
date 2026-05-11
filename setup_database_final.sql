-- =============================================
-- SETUP DATABASE LENGKAP - LANGIT KOREA
-- Versi: Final (Jalankan di Supabase SQL Editor)
-- =============================================

-- 1. Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Tabel profiles (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  nama_lengkap TEXT,
  sekolah_terakhir TEXT,
  tujuan_belajar TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- 3. Tabel progress_unit
CREATE TABLE IF NOT EXISTS public.progress_unit (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE CASCADE,
  unit INTEGER NOT NULL,
  seksi TEXT NOT NULL CHECK (seksi IN ('vocab','grammar','conversation','budaya','mini_test')),
  status TEXT DEFAULT 'not_started' CHECK (status IN ('not_started','in_progress','completed')),
  skor INTEGER,
  completed_at TIMESTAMPTZ,
  UNIQUE(user_id, unit, seksi)
);

ALTER TABLE public.progress_unit ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own progress"
  ON public.progress_unit FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own progress"
  ON public.progress_unit FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own progress"
  ON public.progress_unit FOR UPDATE
  USING (auth.uid() = user_id);

-- 4. Tabel latihan_interaktif
CREATE TABLE IF NOT EXISTS public.latihan_interaktif (
  id SERIAL PRIMARY KEY,
  unit INTEGER NOT NULL,
  seksi TEXT NOT NULL CHECK (seksi IN (
    'vocab1','vocab2','grammar1','grammar2',
    'conversation1','conversation2','budaya'
  )),
  tipe_latihan TEXT NOT NULL CHECK (tipe_latihan IN (
    'flashcard',
    'cocokkan',
    'pilih_kata',
    'lengkapi_dialog',
    'pilihan_ganda',
    'pemahaman_dialog'
  )),
  urutan INTEGER DEFAULT 1,
  teks_korea TEXT,
  teks_indo TEXT,
  teks_inggris TEXT,
  gambar_url TEXT,
  audio_url TEXT,
  pasangan JSONB,
  soal TEXT,
  opsi JSONB,
  jawaban TEXT,
  dialog JSONB,
  konteks TEXT,
  akses TEXT DEFAULT 'free' CHECK (akses IN ('free','premium')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.latihan_interaktif ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read latihan free"
  ON public.latihan_interaktif FOR SELECT
  USING (akses = 'free');

CREATE POLICY "Service role full access latihan"
  ON public.latihan_interaktif FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- 5. Tabel soal_eps (CREATE IF NOT EXISTS + ADD COLUMNS)
CREATE TABLE IF NOT EXISTS public.soal_eps (
  id SERIAL PRIMARY KEY,
  unit INTEGER,
  nomor INTEGER,
  bab INTEGER,
  tipe TEXT CHECK (tipe IN ('membaca','mendengarkan')),
  teks_soal TEXT,
  gambar_url TEXT,
  audio_url TEXT,
  pilihan_a TEXT,
  pilihan_b TEXT,
  pilihan_c TEXT,
  pilihan_d TEXT,
  jawaban_benar TEXT CHECK (jawaban_benar IN ('a','b','c','d')),
  penjelasan TEXT,
  tingkat TEXT CHECK (tingkat IN ('mudah','sedang','sulit')),
  sumber TEXT DEFAULT 'textbook' CHECK (sumber IN ('textbook','open_test')),
  tahun_soal INTEGER,
  nomor_asli INTEGER,
  akses TEXT DEFAULT 'free' CHECK (akses IN ('free','premium')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tambah kolom jika sudah ada tabel tapi belum ada kolomnya
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='soal_eps' AND column_name='sumber') THEN
    ALTER TABLE public.soal_eps ADD COLUMN sumber TEXT DEFAULT 'textbook' CHECK (sumber IN ('textbook','open_test'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='soal_eps' AND column_name='tahun_soal') THEN
    ALTER TABLE public.soal_eps ADD COLUMN tahun_soal INTEGER;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='soal_eps' AND column_name='nomor_asli') THEN
    ALTER TABLE public.soal_eps ADD COLUMN nomor_asli INTEGER;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='soal_eps' AND column_name='akses') THEN
    ALTER TABLE public.soal_eps ADD COLUMN akses TEXT DEFAULT 'free' CHECK (akses IN ('free','premium'));
  END IF;
END $$;

ALTER TABLE public.soal_eps ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read soal_eps"
  ON public.soal_eps FOR SELECT
  USING (true);

CREATE POLICY "Service role full access soal_eps"
  ON public.soal_eps FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- 6. Indexes untuk performa
CREATE INDEX IF NOT EXISTS idx_latihan_unit ON public.latihan_interaktif(unit);
CREATE INDEX IF NOT EXISTS idx_latihan_seksi ON public.latihan_interaktif(seksi);
CREATE INDEX IF NOT EXISTS idx_soal_eps_unit ON public.soal_eps(unit);
CREATE INDEX IF NOT EXISTS idx_soal_eps_tipe ON public.soal_eps(tipe);
CREATE INDEX IF NOT EXISTS idx_soal_eps_sumber ON public.soal_eps(sumber);
CREATE INDEX IF NOT EXISTS idx_progress_user ON public.progress_unit(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_unit ON public.progress_unit(unit);

-- 7. Verifikasi
SELECT '✅ Database setup selesai!' as status;
