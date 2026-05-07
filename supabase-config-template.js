// ============================================
// Konfigurasi Supabase untuk Langit Korea
// GANTI DENGAN KREDENSIAL SUPABASE MILIKMU
// ============================================

// Project URL dari Supabase Dashboard
// Contoh: https://abc123.supabase.co
const SUPABASE_URL = "https://mozmuwrkfsipzfupybwh.supabase.co";

// Anon key dari Supabase Dashboard
// Contoh: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vem11d3JrZnNpcHpmdXB5YndoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTU5NTQsImV4cCI6MjA5MzI3MTk1NH0.RPqu-07AyKygnS_bPhMO_IgXSz2r8jkljPc5TGq7Vzg";

// ============================================
// CARA MENDAPATKAN KREDENSIAL:
// ============================================
// 1. Login ke https://supabase.com/dashboard
// 2. Pilih project yang sudah dibuat
// 3. Klik Settings (ikon roda gigi) → API
// 4. Copy Project URL dan anon key
// 5. Paste di atas
// ============================================

// Inisialisasi Supabase Client
const { createClient } = window.supabase;
const db = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Export untuk digunakan di file lain (via global)
window.SUPABASE_URL = SUPABASE_URL;
window.SUPABASE_ANON_KEY = SUPABASE_ANON_KEY;
window.db = db;

console.log("✅ Supabase config loaded");
console.log("📍 URL:", SUPABASE_URL);
console.log("🔑 Key:", SUPABASE_ANON_KEY ? "***terisi***" : "***KOSONG***");
