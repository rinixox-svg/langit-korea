-- =============================================
-- SCRIPT SETUP ROW LEVEL SECURITY (RLS) - LANGIT KOREA
-- Jalankan script ini di Supabase Dashboard > SQL Editor
-- =============================================

-- 1. ENABLE RLS UNTUK SEMUA TABEL
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE soal_eps ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulasi_hasil ENABLE ROW LEVEL SECURITY;

-- 2. POLICY UNTUK TABEL users
-- User hanya bisa melihat dan mengupdate data mereka sendiri
CREATE POLICY "User can view own profile"
ON users FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "User can update own profile"
ON users FOR UPDATE
USING (auth.uid() = id);

-- 3. POLICY UNTUK TABEL soal_eps
-- Semua user (termasuk yang belum login) bisa baca soal 'free'
CREATE POLICY "Public can read free questions"
ON soal_eps FOR SELECT
USING (akses = 'free');

-- Opsi tambahan: Jika ingin user login bisa baca semua soal (premium logic di client)
-- CREATE POLICY "Authenticated users can read all questions"
-- ON soal_eps FOR SELECT
-- USING (auth.role() = 'authenticated');

-- 4. POLICY UNTUK TABEL progress_user
-- User hanya bisa insert/update progress milik sendiri
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
-- User hanya bisa melihat hasil simulasi mereka sendiri
CREATE POLICY "User can view own results"
ON simulasi_hasil FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "User can insert own results"
ON simulasi_hasil FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- =============================================
-- STORAGE POLICY (UNTUK AUDIO MP3)
-- =============================================
-- Pastikan bucket 'audio-listening' sudah dibuat di Storage

-- Hanya user login yang bisa download audio
CREATE POLICY "Authenticated users can download audio"
ON storage.objects FOR SELECT
USING (bucket_id = 'audio-listening' AND auth.role() = 'authenticated');

-- =============================================
-- CATATAN PENTING
-- =============================================
-- 1. Jalankan script ini di Supabase Dashboard > SQL Editor
-- 2. Pastikan RLS sudah aktif di setiap tabel (centang hijau di Dashboard)
-- 3. Jangan gunakan SERVICE ROLE KEY di frontend, gunakan ANON KEY saja
-- 4. Test kebijakan dengan login sebagai user berbeda

-- VERIFIKASI: Cek apakah RLS sudah aktif
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('users', 'soal_eps', 'progress_user', 'simulasi_hasil');
