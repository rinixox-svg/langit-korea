-- =============================================
-- SETUP TABEL soal_eps - LANGIT KOREA
-- Versi: Final - Safe Re-run
-- Jalankan di Supabase Dashboard > SQL Editor
-- =============================================

-- 1. BUAT TABEL soal_eps (jika belum ada)
CREATE TABLE IF NOT EXISTS public.soal_eps (
    id TEXT PRIMARY KEY,
    bab INTEGER NOT NULL,
    tipe TEXT NOT NULL CHECK (tipe IN ('membaca', 'mendengarkan')),
    teks_soal TEXT NOT NULL,
    gambar_url TEXT DEFAULT '',
    audio_url TEXT DEFAULT '',
    pilihan_a TEXT DEFAULT '',
    pilihan_b TEXT DEFAULT '',
    pilihan_c TEXT DEFAULT '',
    pilihan_d TEXT DEFAULT '',
    jawaban_benar TEXT CHECK (jawaban_benar IN ('a', 'b', 'c', 'd')),
    audio_teks TEXT DEFAULT '',
    penjelasan TEXT DEFAULT '',
    tingkat TEXT DEFAULT 'sedang' CHECK (tingkat IN ('mudah', 'sedang', 'sulit')),
    akses TEXT DEFAULT 'free' CHECK (akses IN ('free', 'premium')),
    sumber_url TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. ENABLE RLS
ALTER TABLE public.soal_eps ENABLE ROW LEVEL SECURITY;

-- 3. BUAT POLICY (dengan pengecekan duplikat menggunakan DO block)
DO $$
BEGIN
    -- Policy: Public read access untuk soal free
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'soal_eps'
        AND policyname = 'Public read free questions'
    ) THEN
        CREATE POLICY "Public read free questions"
        ON public.soal_eps
        FOR SELECT
        USING (akses = 'free' OR akses = 'premium');
    END IF;

    -- Policy: Authenticated users can read all (untuk premium)
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'soal_eps'
        AND policyname = 'Auth read all questions'
    ) THEN
        CREATE POLICY "Auth read all questions"
        ON public.soal_eps
        FOR SELECT
        USING (auth.role() = 'authenticated');
    END IF;

    -- Policy: Service role can insert/update/delete (untuk script upload)
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'soal_eps'
        AND policyname = 'Service role full access'
    ) THEN
        CREATE POLICY "Service role full access"
        ON public.soal_eps
        FOR ALL
        USING (auth.role() = 'service_role')
        WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

-- 4. BUAT INDEX (jika belum ada)
CREATE INDEX IF NOT EXISTS idx_soal_eps_bab ON public.soal_eps(bab);
CREATE INDEX IF NOT EXISTS idx_soal_eps_tipe ON public.soal_eps(tipe);
CREATE INDEX IF NOT EXISTS idx_soal_eps_akses ON public.soal_eps(akses);

-- 5. VERIFIKASI
SELECT 'Tabel soal_eps berhasil dibuat!' as status;
SELECT COUNT(*) as jumlah_soal FROM public.soal_eps;
