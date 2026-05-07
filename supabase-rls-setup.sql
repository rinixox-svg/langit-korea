-- =============================================
-- SCRIPT SETUP ROW LEVEL SECURITY (RLS) - LANGIT KOREA
-- Versi: Safe Re-run (Bisa dijalankan berkali-kali)
-- Jalankan script ini di Supabase Dashboard > SQL Editor
-- =============================================

-- 1. ENABLE RLS UNTUK SEMUA TABEL
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE soal_eps ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulasi_hasil ENABLE ROW LEVEL SECURITY;

-- 2. POLICY UNTUK TABEL users
-- Hapus policy lama jika ada, lalu buat baru
DROP POLICY IF EXISTS "User can view own profile" ON users;
DROP POLICY IF EXISTS "User can update own profile" ON users;

CREATE POLICY "User can view own profile"
ON users FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "User can update own profile"
ON users FOR UPDATE
USING (auth.uid() = id);

-- 3. POLICY UNTUK TABEL soal_eps
DROP POLICY IF EXISTS "Public can read free questions" ON soal_eps;

CREATE POLICY "Public can read free questions"
ON soal_eps FOR SELECT
USING (akses = 'free');

-- 4. POLICY UNTUK TABEL progress_user
DROP POLICY IF EXISTS "User can insert own progress" ON progress_user;
DROP POLICY IF EXISTS "User can view own progress" ON progress_user;
DROP POLICY IF EXISTS "User can update own progress" ON progress_user;

CREATE POLICY "User can insert own progress"
ON progress_user FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "User can view own progress"
ON progress_user FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "User can update own progress"
ON progress_user FOR UPDATE
USING (auth.uid() = user_id);

-- 5. POLICY UNTUK TABEL simulasi_hasil
DROP POLICY IF EXISTS "User can view own results" ON simulasi_hasil;
DROP POLICY IF EXISTS "User can insert own results" ON simulasi_hasil;

CREATE POLICY "User can view own results"
ON simulasi_hasil FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "User can insert own results"
ON simulasi_hasil FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- =============================================
-- STORAGE POLICY (UNTUK AUDIO MP3)
-- =============================================
DROP POLICY IF EXISTS "Authenticated users can download audio" ON storage.objects;

CREATE POLICY "Authenticated users can download audio"
ON storage.objects FOR SELECT
USING (bucket_id = 'audio-listening' AND auth.role() = 'authenticated');

-- =============================================
-- VERIFIKASI
-- =============================================
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('users', 'soal_eps', 'progress_user', 'simulasi_hasil');
