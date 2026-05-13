-- ============================================================
-- LANGIT KOREA — Future-Proofing: Unique Constraints & Soft Delete
-- ============================================================
-- Jalankan SETELAH duplikat dibersihkan (lihat dedup_detection.sql)
-- ============================================================

-- ═══════════════════════════════════════════════════════════════
-- BAGIAN 3A: UNIQUE CONSTRAINT — Standard (tanpa soft-delete)
-- ═══════════════════════════════════════════════════════════════

-- ── 3A.1 soal_eps ──
-- Kolom identifier: sumber, unit, nomor_asli, tipe
-- (sumber='open_test' + tahun_soal + nomor_asli = 1 record)
-- (sumber='textbook' + unit + tipe = max 1 record)
ALTER TABLE [nama_tabel_soal_eps]
ADD CONSTRAINT [nama_constraint_soal_eps]
UNIQUE ([kolom_sumber], [kolom_unit], [kolom_nomor_asli], [kolom_tipe]);

-- Contoh konkret untuk soal_eps:
-- ALTER TABLE soal_eps
-- ADD CONSTRAINT soal_eps_unique_key
-- UNIQUE (sumber, unit, nomor_asli, tipe);


-- ── 3A.2 latihan_interaktif ──
-- Kolom identifier: unit, seksi, tipe_latihan, urutan
ALTER TABLE [nama_tabel_latihan_interaktif]
ADD CONSTRAINT [nama_constraint_latihan_interaktif]
UNIQUE ([kolom_unit], [kolom_seksi], [kolom_tipe_latihan], [kolom_urutan]);

-- Contoh:
-- ALTER TABLE latihan_interaktif
-- ADD CONSTRAINT latihan_interaktif_unique_key
-- UNIQUE (unit, seksi, tipe_latihan, urutan);


-- ── 3A.3 materi_unit ──
-- Kolom identifier: unit, kategori, sub
ALTER TABLE [nama_tabel_materi_unit]
ADD CONSTRAINT [nama_constraint_materi_unit]
UNIQUE ([kolom_unit], [kolom_kategori], [kolom_sub]);

-- Contoh:
-- ALTER TABLE materi_unit
-- ADD CONSTRAINT materi_unit_unique_key
-- UNIQUE (unit, kategori, sub);


-- ── 3A.4 progress_unit ──
-- Kolom identifier: user_id, unit_id, seksi
ALTER TABLE [nama_tabel_progress_unit]
ADD CONSTRAINT [nama_constraint_progress_unit]
UNIQUE ([kolom_user_id], [kolom_unit_id], [kolom_seksi]);

-- Contoh:
-- ALTER TABLE progress_unit
-- ADD CONSTRAINT progress_unit_user_unit_seksi_key
-- UNIQUE (user_id, unit_id, seksi);
--
-- Catatan: UNIQUE constraint ini hanya akan digunakan
-- oleh aplikasi sebagai panduan, BUKAN diaktifkan secara penuh
-- karena constraint UNIQUE akan bentrok dengan proses retry
-- dari client yang melakukan UPDATE progress.


-- ═══════════════════════════════════════════════════════════════
-- BAGIAN 3B: UNIQUE INDEX + Soft-Delete Handling
-- ═══════════════════════════════════════════════════════════════

/*
 * ── PROBLEM ──
 * Jika tabel menggunakan soft-delete (kolom deleted_at),
 * UNIQUE CONSTRAINT biasa akan GAGAL karena baris yang di-soft-delete
 * tetap dianggap bertentangan dengan baris aktif.
 *
 * Contoh: user_id=1, unit_id=31, seksi='vocab1' -> deleted_at = NOW()
 * User mencoba insert ulang dengan nilai yang sama -> CONSTRAINT VIOLATION
 *
 * ── SOLUSI ──
 * Gunakan PARTIAL UNIQUE INDEX (unique index dengan WHERE clause)
 * yang hanya berlaku untuk baris dengan deleted_at IS NULL.
 * Ini adalah fitur PostgreSQL yang TIDAK tersedia di MySQL.
 */

-- ── 3B.1 Partial Unique Index untuk progress_unit (soft-delete ready) ──
CREATE UNIQUE INDEX IF NOT EXISTS [nama_index_progress_unit_aktif]
ON [nama_tabel_progress_unit] ([kolom_user_id], [kolom_unit_id], [kolom_seksi])
WHERE [kolom_deleted_at] IS NULL;

-- Contoh:
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_progress_unit_active
-- ON progress_unit (user_id, unit_id, seksi)
-- WHERE deleted_at IS NULL;


-- ── 3B.2 Partial Unique Index untuk tabel lain jika perlu soft-delete ──
-- Template:
-- CREATE UNIQUE INDEX IF NOT EXISTS [nama_index]
-- ON [nama_tabel] ([kolom_identifier_1], [kolom_identifier_2])
-- WHERE [kolom_deleted_at] IS NULL;


-- ── 3B.3 Cek existing indexes ──
-- Jalankan ini untuk melihat index apa saja yang sudah ada:
SELECT
    tablename as tabel,
    indexname as nama_index,
    indexdef as definisi
FROM pg_indexes
WHERE tablename IN ('soal_eps', 'latihan_interaktif', 'materi_unit', 'progress_unit')
ORDER BY tablename, indexname;


-- ── 3B.4 Cek existing constraints ──
-- Jalankan ini untuk melihat constraint apa saja yang sudah ada:
SELECT
    tc.table_name as tabel,
    tc.constraint_name as nama_constraint,
    tc.constraint_type as tipe
FROM information_schema.table_constraints tc
WHERE tc.table_name IN ('soal_eps', 'latihan_interaktif', 'materi_unit', 'progress_unit')
ORDER BY tc.table_name, tc.constraint_name;

-- Detail kolom dalam constraint:
SELECT
    tc.table_name as tabel,
    tc.constraint_name,
    kcu.column_name as kolom
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.table_name IN ('soal_eps', 'latihan_interaktif', 'materi_unit', 'progress_unit')
ORDER BY tc.table_name, tc.constraint_name, kcu.ordinal_position;


-- ═══════════════════════════════════════════════════════════════
-- BAGIAN 3C: HAPUS CONSTRAINT / INDEX (Jika perlu rollback)
-- ═══════════════════════════════════════════════════════════════

-- Hapus UNIQUE CONSTRAINT:
-- ALTER TABLE [nama_tabel] DROP CONSTRAINT [nama_constraint];

-- Hapus UNIQUE INDEX:
-- DROP INDEX IF EXISTS [nama_index];

-- Contoh:
-- ALTER TABLE soal_eps DROP CONSTRAINT IF EXISTS soal_eps_unique_key;
-- DROP INDEX IF EXISTS idx_progress_unit_active;


-- ═══════════════════════════════════════════════════════════════
-- BAGIAN 3D: TEST CONSTRAINT (Sebelum diaktifkan)
-- ═══════════════════════════════════════════════════════════════

-- Test apakah insert data baru akan melanggar constraint:
-- (Jalankan di transaksi agar tidak jadi benar-benar insert)
-- BEGIN;
--   INSERT INTO soal_eps (sumber, unit, nomor_asli, tipe)
--   VALUES ('open_test', 2023, 1, 'membaca');
--   -- Harusnya error: duplicate key violates unique constraint
-- ROLLBACK;
--
-- Jika error muncul = constraint BEKERJA ✅
-- Jika sukses (tidak error) = ada duplikat yang belum dibersihkan ❌


-- ═══════════════════════════════════════════════════════════════
-- BAGIAN 3E: ALTERNATIF — ON CONFLICT (Untuk aplikasi)
-- ═══════════════════════════════════════════════════════════════

/*
 * Untuk mencegah duplikat dari SISI APLIKASI (bukan dari database),
 * gunakan INSERT ... ON CONFLICT DO UPDATE (upsert).
 *
 * Contoh di aplikasi Python (supabase-py):
 *
 *   supabase.table("soal_eps").upsert(row, on_conflict="sumber,unit,nomor_asli,tipe").execute()
 *
 * Contoh di aplikasi JavaScript (supabase-js):
 *
 *   supabase.from("soal_eps").upsert(row, { onConflict: 'sumber,unit,nomor_asli,tipe' })
 *
 * Ini sudah kita terapkan di extract_open_test.py:
 *   supabase.table("soal_eps").upsert(row, on_conflict="sumber,unit,nomor_asli,tipe").execute()
 *
 * CATATAN: upsert membutuhkan UNIQUE INDEX atau UNIQUE CONSTRAINT
 * agar PostgreSQL tahu cara mendeteksi konflik.
 */
