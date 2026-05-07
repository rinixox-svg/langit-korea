/**
 * KONFIGURASI SUPABASE UNTUK LANGIT KOREA
 *
 * CARA PENGGUNAAN:
 * 1. Copy file ini menjadi `supabase-config.js`
 * 2. Isi SUPABASE_URL dan SUPABASE_ANON_KEY dengan milikmu
 * 3. JANGAN commit `supabase-config.js` ke repository (sudah ada di .gitignore)
 *
 * Dapatkan credentials di: Supabase Dashboard > Project Settings > API
 */

// GANTI DENGAN MILIKMU - Jangan hapus komentar ini agar tidak tertukar
const SUPABASE_URL = 'https://xyz.supabase.co'; // GANTI DENGAN MILIKMU
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'; // GANTI DENGAN MILIKMU

// Inisialisasi Supabase Client
const supabase = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Export untuk digunakan di file lain (jika pakai module)
// export { supabase };
