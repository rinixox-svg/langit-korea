-- ============================================================
-- LANGIT KOREA — Deteksi & Pembersihan Data Duplikat
-- ============================================================
-- Jalankan di Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- ============================================================
-- BAGIAN 1: DETEKSI DUPLIKAT PER TABEL
-- ============================================================

-- ── 1A. soal_eps ──
-- Natural key: (sumber, tahun_soal, nomor_asli, tipe)
-- Unit textbook: (sumber='textbook', unit, tipe, teks_soal)
-- Unit open test: (sumber='open_test', tahun_soal, nomor_asli)

-- Cek duplikat di soal_eps berdasarkan (sumber, unit, nomor_asli, tipe)
SELECT 'soal_eps' as tabel,
       COUNT(*) as total_baris,
       SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) as baris_duplikat,
       COUNT(CASE WHEN cnt > 1 THEN 1 END) as grup_duplikat,
       ROUND(100.0 * SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) / COUNT(*), 1) as pct_duplikat
FROM (
  SELECT COUNT(*) as cnt
  FROM soal_eps
  GROUP BY sumber, unit, nomor_asli, tipe
) sub;

-- Detail grup duplikat soal_eps
WITH duplikat AS (
  SELECT sumber, unit, nomor_asli, tipe, COUNT(*) as cnt,
         array_agg(id ORDER BY created_at) as ids,
         array_agg(created_at::text ORDER BY created_at) as created_times
  FROM soal_eps
  GROUP BY sumber, unit, nomor_asli, tipe
  HAVING COUNT(*) > 1
)
SELECT 'soal_eps' as tabel,
       sumber, unit, nomor_asli, tipe,
       cnt as jumlah_duplikat,
       ids,
       created_times
FROM duplikat
ORDER BY cnt DESC, sumber, unit, nomor_asli;

-- ── 1B. latihan_interaktif ──
-- Natural key: (unit, seksi, tipe_latihan, urutan)

SELECT 'latihan_interaktif' as tabel,
       COUNT(*) as total_baris,
       SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) as baris_duplikat,
       COUNT(CASE WHEN cnt > 1 THEN 1 END) as grup_duplikat,
       ROUND(100.0 * SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) / COUNT(*), 1) as pct_duplikat
FROM (
  SELECT COUNT(*) as cnt
  FROM latihan_interaktif
  GROUP BY unit, seksi, tipe_latihan, urutan
) sub;

-- Detail grup duplikat latihan_interaktif
WITH duplikat AS (
  SELECT unit, seksi, tipe_latihan, urutan, COUNT(*) as cnt,
         array_agg(id ORDER BY created_at) as ids,
         array_agg(created_at::text ORDER BY created_at) as created_times
  FROM latihan_interaktif
  GROUP BY unit, seksi, tipe_latihan, urutan
  HAVING COUNT(*) > 1
)
SELECT 'latihan_interaktif' as tabel,
       unit, seksi, tipe_latihan, urutan,
       cnt as jumlah_duplikat,
       ids,
       created_times
FROM duplikat
ORDER BY cnt DESC, unit, seksi;

-- ── 1C. materi_unit ──
-- Natural key: (unit, kategori, sub)

SELECT 'materi_unit' as tabel,
       COUNT(*) as total_baris,
       SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) as baris_duplikat,
       COUNT(CASE WHEN cnt > 1 THEN 1 END) as grup_duplikat,
       ROUND(100.0 * SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) / COUNT(*), 1) as pct_duplikat
FROM (
  SELECT COUNT(*) as cnt
  FROM materi_unit
  GROUP BY unit, kategori, sub
) sub;

-- Detail grup duplikat materi_unit
WITH duplikat AS (
  SELECT unit, kategori, sub, COUNT(*) as cnt,
         array_agg(id ORDER BY created_at) as ids,
         array_agg(created_at::text ORDER BY created_at) as created_times
  FROM materi_unit
  GROUP BY unit, kategori, sub
  HAVING COUNT(*) > 1
)
SELECT 'materi_unit' as tabel,
       unit, kategori, sub,
       cnt as jumlah_duplikat,
       ids,
       created_times
FROM duplikat
ORDER BY cnt DESC, unit, kategori, sub;

-- ── 1D. progress_unit ──
-- Natural key: (user_id, unit_id, seksi)

SELECT 'progress_unit' as tabel,
       COUNT(*) as total_baris,
       SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) as baris_duplikat,
       COUNT(CASE WHEN cnt > 1 THEN 1 END) as grup_duplikat,
       ROUND(100.0 * SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) / COUNT(*), 1) as pct_duplikat
FROM (
  SELECT COUNT(*) as cnt
  FROM progress_unit
  GROUP BY user_id, unit_id, seksi
) sub;


-- ============================================================
-- BAGIAN 2: PREVIEW DATA YANG AKAN DIHAPUS (SEBELUM DELETE)
-- ============================================================

-- ── 2A. Preview duplikat soal_eps yang akan dihapus ──
-- Strategi: simpan baris dengan created_at PALING LAMA, hapus sisanya
-- Ganti WHERE clause sesuai tabel yang ingin dibersihkan

WITH ranked AS (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY sumber, unit, nomor_asli, tipe
           ORDER BY created_at ASC  -- simpan yang PALING TUA (pertama masuk)
         ) as rn
  FROM soal_eps
)
SELECT 'AKAN DIHAPUS' as aksi, id, sumber, unit, nomor_asli, tipe, jawaban, created_at
FROM ranked
WHERE rn > 1
ORDER BY sumber, unit, nomor_asli, tipe, created_at;

-- ── 2B. Preview duplikat latihan_interaktif yang akan dihapus ──
WITH ranked AS (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY unit, seksi, tipe_latihan, urutan
           ORDER BY created_at ASC
         ) as rn
  FROM latihan_interaktif
)
SELECT 'AKAN DIHAPUS' as aksi, id, unit, seksi, tipe_latihan, urutan, created_at
FROM ranked
WHERE rn > 1
ORDER BY unit, seksi, tipe_latihan, urutan, created_at;

-- ── 2C. Preview duplikat materi_unit yang akan dihapus ──
WITH ranked AS (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY unit, kategori, sub
           ORDER BY created_at ASC
         ) as rn
  FROM materi_unit
)
SELECT 'AKAN DIHAPUS' as aksi, id, unit, kategori, sub, created_at
FROM ranked
WHERE rn > 1
ORDER BY unit, kategori, sub, created_at;


-- ============================================================
-- BAGIAN 3: EKSEKUSI PENGHAPUSAN (SETELAH PREVIEW DISETUJUI)
-- ============================================================
-- HAPUS komen komentar baris di bawah SETELAH preview diverifikasi
-- Jalankan SATU PER SATU, bukan sekaligus

-- ⚠️ HAPUS duplikat soal_eps (cadangkan dulu!)
-- BEGIN;
--   WITH ranked AS (
--     SELECT id,
--            ROW_NUMBER() OVER (
--              PARTITION BY sumber, unit, nomor_asli, tipe
--              ORDER BY created_at ASC
--            ) as rn
--     FROM soal_eps
--   )
--   DELETE FROM soal_eps
--   WHERE id IN (
--     SELECT id FROM ranked WHERE rn > 1
--   );
-- COMMIT;

-- ⚠️ HAPUS duplikat latihan_interaktif
-- BEGIN;
--   WITH ranked AS (
--     SELECT id,
--            ROW_NUMBER() OVER (
--              PARTITION BY unit, seksi, tipe_latihan, urutan
--              ORDER BY created_at ASC
--            ) as rn
--     FROM latihan_interaktif
--   )
--   DELETE FROM latihan_interaktif
--   WHERE id IN (
--     SELECT id FROM ranked WHERE rn > 1
--   );
-- COMMIT;

-- ⚠️ HAPUS duplikat materi_unit
-- BEGIN;
--   WITH ranked AS (
--     SELECT id,
--            ROW_NUMBER() OVER (
--              PARTITION BY unit, kategori, sub
--              ORDER BY created_at ASC
--            ) as rn
--     FROM materi_unit
--   )
--   DELETE FROM materi_unit
--   WHERE id IN (
--     SELECT id FROM ranked WHERE rn > 1
--   );
-- COMMIT;


-- ============================================================
-- BAGIAN 4: PREVENTIF — Tambah Unique Constraint
-- ============================================================
-- Jalankan SETELAH duplikat dibersihkan, untuk mencegah kejadian serupa

-- Cek apakah ada duplikat dulu sebelum tambah constraint
-- (jalankan Bagian 1 dulu, pastikan hasilnya 0)

-- ⚠️ Tambah unique constraint (hanya jika duplikat sudah 0)
-- ALTER TABLE soal_eps ADD CONSTRAINT soal_eps_unique_key
--   UNIQUE (sumber, unit, nomor_asli, tipe);

-- ALTER TABLE latihan_interaktif ADD CONSTRAINT latihan_interaktif_unique_key
--   UNIQUE (unit, seksi, tipe_latihan, urutan);

-- ALTER TABLE materi_unit ADD CONSTRAINT materi_unit_unique_key
--   UNIQUE (unit, kategori, sub);


-- ============================================================
-- BAGIAN 5: RINGKASAN SEMUA TABEL
-- ============================================================

WITH stats AS (
  SELECT 'soal_eps' as tbl, COUNT(*) as total FROM soal_eps
  UNION ALL
  SELECT 'latihan_interaktif', COUNT(*) FROM latihan_interaktif
  UNION ALL
  SELECT 'materi_unit', COUNT(*) FROM materi_unit
  UNION ALL
  SELECT 'progress_unit', COUNT(*) FROM progress_unit
  UNION ALL
  SELECT 'gambar_materi', COUNT(*) FROM gambar_materi
  UNION ALL
  SELECT 'profiles', COUNT(*) FROM profiles
)
SELECT tbl as "Tabel", total as "Total Baris"
FROM stats
ORDER BY total DESC;
