# 🌌 LANGIT KOREA — BACKEND PROMPT (OPSI A)
> Taruh ini sebagai System Prompt di Zed AI Assistant.
> Ini MELENGKAPI prompt utama langit-korea-prompt.md — taruh keduanya sekaligus.

---

## 🏗️ ARSITEKTUR BACKEND (OPSI A — TANPA LARAVEL, 100% GRATIS)

```
Browser User
    ↕  langsung (tidak ada server perantara)
Supabase (satu platform, semua fungsi)
  ├── Auth      → login, daftar, session user
  ├── Database  → PostgreSQL (soal, progress, hasil)
  ├── Storage   → file audio MP3, PDF modul
  └── RLS       → keamanan akses data per user
    ↕  hanya untuk fitur premium AI
Anthropic Claude API → evaluasi jawaban menulis
```

**Tidak ada Laravel. Tidak ada server PHP. Tidak ada Railway.**
Frontend HTML/JS berbicara langsung ke Supabase dari browser.

---

## ⚙️ CARA SUPABASE DIINISIALISASI (WAJIB ADA DI SETIAP FILE)

```html
<!-- Taruh di bagian <head> setiap file HTML -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

<script>
  // GANTI DENGAN MILIKMU — ambil dari: supabase.com → project → Settings → API
  const SUPABASE_URL  = 'https://XXXXXXXXXXX.supabase.co'
  const SUPABASE_ANON = 'eyXXXXXXXXXXXXXXXXXXXXXXXXXX'  // anon/public key SAJA

  // Inisialisasi client — satu kali, dipakai semua fungsi di bawahnya
  const { createClient } = supabase
  const db = createClient(SUPABASE_URL, SUPABASE_ANON)
</script>
```

### ⚠️ ATURAN KEAMANAN WAJIB — JANGAN DILANGGAR:
- **HANYA gunakan `anon` key** di file HTML (yang bisa dilihat semua orang)
- **JANGAN PERNAH** taruh `service_role` key di HTML/JS — ini key admin yang bisa bypass semua keamanan
- **Selalu aktifkan RLS** di setiap tabel sebelum go live
- Tanpa RLS aktif → semua data bisa dibaca siapa saja yang punya URL project kamu

---

## 🗄️ STRUKTUR DATABASE POSTGRESQL

### SQL Setup — jalankan di Supabase SQL Editor:

```sql
-- ============================================================
-- TABEL 1: profiles (data user, extend dari auth.users)
-- ============================================================
CREATE TABLE public.profiles (
  id          uuid REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  nama        text,
  status      text DEFAULT 'free' CHECK (status IN ('free', 'premium')),
  token_unlock integer DEFAULT 0,
  hangul_lulus boolean DEFAULT false,
  created_at  timestamptz DEFAULT now()
);

-- Aktifkan RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Policy: user hanya bisa lihat & edit profil sendiri
CREATE POLICY "User lihat profil sendiri"
  ON public.profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "User edit profil sendiri"
  ON public.profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

-- Auto-buat profil saat user baru daftar
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id)
  VALUES (new.id);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ============================================================
-- TABEL 2: soal_hangul (latihan huruf Korea dasar)
-- ============================================================
CREATE TABLE public.soal_hangul (
  id          serial PRIMARY KEY,
  huruf       text NOT NULL,           -- contoh: 'ㄱ'
  romanisasi  text NOT NULL,           -- contoh: 'g/k'
  contoh_kata text,                    -- contoh: '가방 (gabang)'
  pilihan     jsonb NOT NULL,          -- ["ㄱ","ㄴ","ㄷ","ㄹ"]
  jawaban     text NOT NULL,           -- 'ㄱ'
  tipe        text DEFAULT 'konsonan', -- 'vokal' atau 'konsonan'
  urutan      integer DEFAULT 0
);

ALTER TABLE public.soal_hangul ENABLE ROW LEVEL SECURITY;

-- Soal hangul bisa dibaca semua orang (gratis)
CREATE POLICY "Soal hangul publik"
  ON public.soal_hangul FOR SELECT
  TO anon, authenticated
  USING (true);


-- ============================================================
-- TABEL 3: soal_eps (bank soal EPS-TOPIK)
-- ============================================================
CREATE TABLE public.soal_eps (
  id           serial PRIMARY KEY,
  unit         integer NOT NULL,            -- 31-60 sesuai textbook HRD Korea
  tipe         text NOT NULL CHECK (tipe IN ('membaca', 'mendengarkan')),
  teks_soal    text NOT NULL,
  gambar_url   text,                        -- opsional, URL dari Supabase Storage
  audio_url    text,                        -- opsional, URL MP3 dari Supabase Storage
  pilihan_a    text NOT NULL,
  pilihan_b    text NOT NULL,
  pilihan_c    text NOT NULL,
  pilihan_d    text NOT NULL,
  jawaban      text NOT NULL CHECK (jawaban IN ('a','b','c','d')),
  penjelasan   text,                        -- penjelasan jawaban, bahasa Indonesia
  tingkat      text DEFAULT 'sedang' CHECK (tingkat IN ('mudah','sedang','sulit')),
  akses        text DEFAULT 'free' CHECK (akses IN ('free','premium'))
);

ALTER TABLE public.soal_eps ENABLE ROW LEVEL SECURITY;

-- Soal gratis: bisa dibaca semua orang
CREATE POLICY "Soal free bisa dibaca semua"
  ON public.soal_eps FOR SELECT
  TO anon, authenticated
  USING (akses = 'free');

-- Soal premium: hanya user premium
CREATE POLICY "Soal premium hanya untuk premium"
  ON public.soal_eps FOR SELECT
  TO authenticated
  USING (
    akses = 'free'
    OR (
      akses = 'premium'
      AND EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid()
        AND status = 'premium'
      )
    )
  );


-- ============================================================
-- TABEL 4: progress_user (jawaban per soal per user)
-- ============================================================
CREATE TABLE public.progress_user (
  id            uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  soal_id       integer NOT NULL,
  tipe_soal     text NOT NULL CHECK (tipe_soal IN ('hangul','eps')),
  jawaban_user  text,
  benar         boolean NOT NULL,
  dikerjakan_at timestamptz DEFAULT now()
);

ALTER TABLE public.progress_user ENABLE ROW LEVEL SECURITY;

-- User hanya bisa akses progress milik sendiri
CREATE POLICY "User kelola progress sendiri"
  ON public.progress_user FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);


-- ============================================================
-- TABEL 5: simulasi_hasil (hasil simulasi ujian)
-- ============================================================
CREATE TABLE public.simulasi_hasil (
  id              uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id         uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  skor_membaca    integer DEFAULT 0,
  skor_mendengar  integer DEFAULT 0,
  skor_total      integer DEFAULT 0,
  total_soal      integer DEFAULT 0,
  durasi_detik    integer DEFAULT 0,
  selesai_at      timestamptz DEFAULT now()
);

ALTER TABLE public.simulasi_hasil ENABLE ROW LEVEL SECURITY;

-- User hanya bisa akses hasil milik sendiri
CREATE POLICY "User kelola hasil simulasi sendiri"
  ON public.simulasi_hasil FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```

---

## 📦 POLA KODE JAVASCRIPT — SIAP PAKAI

### AUTH: Daftar Akun Baru
```javascript
async function daftarAkun(email, password, nama) {
  // Tampilkan loading
  tampilkanLoading(true)

  const { data, error } = await db.auth.signUp({
    email: email,
    password: password,
    options: {
      data: { nama: nama }  // disimpan di user metadata
    }
  })

  tampilkanLoading(false)

  if (error) {
    tampilkanPesan('Gagal daftar: ' + error.message, 'error')
    return
  }

  tampilkanPesan('Berhasil! Cek email kamu untuk konfirmasi.', 'sukses')
}
```

### AUTH: Login
```javascript
async function login(email, password) {
  tampilkanLoading(true)

  const { data, error } = await db.auth.signInWithPassword({
    email: email,
    password: password
  })

  tampilkanLoading(false)

  if (error) {
    tampilkanPesan('Email atau password salah.', 'error')
    return
  }

  // Simpan session — Supabase otomatis simpan di localStorage
  // Langsung redirect ke home
  window.location.href = 'home.html'
}
```

### AUTH: Cek Status Login (taruh di setiap halaman yang butuh login)
```javascript
// Taruh di bagian atas script setiap halaman
async function cekLogin() {
  const { data: { session } } = await db.auth.getSession()

  if (!session) {
    // Belum login, redirect ke halaman login
    window.location.href = 'index.html'
    return null
  }

  return session.user
}

// Penggunaan:
const user = await cekLogin()
if (!user) return  // sudah redirect, stop eksekusi
```

### AUTH: Logout
```javascript
async function logout() {
  await db.auth.signOut()
  window.location.href = 'index.html'
}
```

### DATABASE: Ambil Soal EPS (dengan loading & error handling)
```javascript
async function ambilSoalEPS(unit, tipe, limit = 10) {
  tampilkanLoading(true)

  const { data: soal, error } = await db
    .from('soal_eps')
    .select('*')
    .eq('unit', unit)
    .eq('tipe', tipe)
    .limit(limit)
    .order('id')

  tampilkanLoading(false)

  if (error) {
    tampilkanPesan('Tidak bisa memuat soal. Coba lagi ya.', 'error')
    return []
  }

  return soal || []
}
```

### DATABASE: Simpan Jawaban User
```javascript
async function simpanJawaban(soalId, tipesoal, jawabanUser, benar) {
  const user = await cekLogin()
  if (!user) return

  const { error } = await db
    .from('progress_user')
    .insert({
      user_id:      user.id,
      soal_id:      soalId,
      tipe_soal:    tipesoal,
      jawaban_user: jawabanUser,
      benar:        benar
    })

  if (error) {
    console.log('Gagal simpan jawaban:', error.message)
    // Tidak tampilkan error ke user, lanjutkan saja
  }
}
```

### DATABASE: Ambil Profil & Cek Status Premium
```javascript
async function ambilProfil() {
  const user = await cekLogin()
  if (!user) return null

  const { data: profil, error } = await db
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  if (error) return null

  return profil
}

async function apakahPremium() {
  const profil = await ambilProfil()
  return profil?.status === 'premium'
}
```

### DATABASE: Simpan Hasil Simulasi
```javascript
async function simpanHasilSimulasi(skorMembaca, skorMendengar, totalSoal, durasiDetik) {
  const user = await cekLogin()
  if (!user) return

  const skorTotal = skorMembaca + skorMendengar

  const { data, error } = await db
    .from('simulasi_hasil')
    .insert({
      user_id:        user.id,
      skor_membaca:   skorMembaca,
      skor_mendengar: skorMendengar,
      skor_total:     skorTotal,
      total_soal:     totalSoal,
      durasi_detik:   durasiDetik
    })
    .select()
    .single()

  if (error) {
    tampilkanPesan('Gagal menyimpan hasil. Tapi skor kamu: ' + skorTotal, 'warning')
    return null
  }

  return data
}
```

### STORAGE: Ambil URL Audio Listening
```javascript
function ambilURLAudio(namaFile) {
  // namaFile contoh: 'unit-31-soal-1.mp3'
  const { data } = db.storage
    .from('audio-listening')      // nama bucket di Supabase Storage
    .getPublicUrl(namaFile)

  return data.publicUrl
}

// Penggunaan:
const urlAudio = ambilURLAudio('unit-31-soal-1.mp3')
const audioPlayer = document.getElementById('audio-player')
audioPlayer.src = urlAudio
audioPlayer.play()
```

### UNLOCK PREMIUM: Tambah Token & Upgrade Premium
```javascript
async function tambahTokenUnlock() {
  const user = await cekLogin()
  if (!user) return

  // Ambil token saat ini
  const profil = await ambilProfil()
  const tokenSekarang = profil?.token_unlock || 0
  const tokenBaru = tokenSekarang + 1

  const { error } = await db
    .from('profiles')
    .update({ token_unlock: tokenBaru })
    .eq('id', user.id)

  if (!error) {
    tampilkanPesan('Token unlock bertambah! Total: ' + tokenBaru, 'sukses')

    // Jika sudah 5 token, upgrade ke premium
    if (tokenBaru >= 5) {
      await upgradePremium()
    }
  }
}

async function upgradePremium() {
  const user = await cekLogin()
  if (!user) return

  const { error } = await db
    .from('profiles')
    .update({ status: 'premium', token_unlock: 0 })
    .eq('id', user.id)

  if (!error) {
    tampilkanPesan('Selamat! Kamu sekarang sudah Premium 🎉', 'sukses')
  }
}
```

---

## 🔧 FUNGSI HELPER UI (TARUH DI SETIAP FILE)

```javascript
// Tampilkan/sembunyikan loading spinner
function tampilkanLoading(aktif) {
  const el = document.getElementById('loading')
  if (el) el.style.display = aktif ? 'flex' : 'none'
}

// Tampilkan pesan ke user (bukan alert, tapi pesan di dalam halaman)
function tampilkanPesan(teks, tipe = 'info') {
  const el = document.getElementById('pesan')
  if (!el) return

  el.textContent = teks
  el.className = 'pesan pesan-' + tipe  // pesan-sukses / pesan-error / pesan-warning
  el.style.display = 'block'

  // Hilang otomatis setelah 4 detik
  setTimeout(() => { el.style.display = 'none' }, 4000)
}
```

---

## 📁 SETUP SUPABASE STORAGE (Lakukan sekali di dashboard)

```
Di Supabase Dashboard:
1. Storage → New Bucket → nama: "audio-listening"  → Public: YES
2. Storage → New Bucket → nama: "modul-pdf"         → Public: NO (premium saja)
3. Storage → New Bucket → nama: "gambar-soal"       → Public: YES

Untuk bucket "modul-pdf" (private), tambahkan policy:
- SELECT: hanya user dengan status premium di tabel profiles
```

---

## 🔐 SQL POLICY UNTUK STORAGE (jalankan di SQL Editor)

```sql
-- Audio listening: bisa diakses semua orang (termasuk yang belum login)
CREATE POLICY "Audio publik untuk semua"
  ON storage.objects FOR SELECT
  TO anon, authenticated
  USING (bucket_id = 'audio-listening');

-- Gambar soal: bisa diakses semua orang
CREATE POLICY "Gambar soal publik untuk semua"
  ON storage.objects FOR SELECT
  TO anon, authenticated
  USING (bucket_id = 'gambar-soal');

-- PDF modul: hanya user premium
CREATE POLICY "PDF modul hanya untuk premium"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'modul-pdf'
    AND EXISTS (
      SELECT 1 FROM public.profiles
      WHERE id = auth.uid()
      AND status = 'premium'
    )
  );
```

---

## 🌐 SETUP VERCEL (Hosting Frontend — Gratis)

```
Langkah deploy ke Vercel:
1. Upload semua file HTML/CSS/JS ke GitHub (repo baru: langit-korea)
2. Buka vercel.com → Import Project → pilih repo langit-korea
3. Framework: Other (bukan Next.js, bukan React)
4. Build Command: kosongkan
5. Output Directory: kosongkan (atau titik ".")
6. Deploy → dapat URL: langitkorea.vercel.app (gratis)

Setiap kali kamu push ke GitHub → Vercel auto-deploy otomatis
```

---

## ✅ CHECKLIST SEBELUM GO LIVE

```
[ ] SUPABASE_URL dan SUPABASE_ANON sudah diganti di semua file
[ ] JANGAN ada service_role key di file HTML/JS manapun
[ ] RLS sudah aktif di semua tabel (cek di Supabase Dashboard → Table Editor → tiap tabel)
[ ] Minimal 1 policy ada di setiap tabel
[ ] Bucket storage sudah dibuat (audio-listening, modul-pdf, gambar-soal)
[ ] Test login/daftar di browser sebelum deploy
[ ] Test akses soal free dan premium dengan akun berbeda
```

---

## ⚠️ ATURAN CODING KHUSUS BACKEND (TAMBAHAN DARI PROMPT UTAMA)

1. **Selalu async/await** untuk semua fungsi Supabase — tidak ada callback, tidak ada .then()
2. **Selalu cek error** dari setiap query Supabase: `const { data, error } = await db...`
3. **Jangan tampilkan error teknis** ke user — terjemahkan jadi pesan ramah Bahasa Indonesia
4. **Selalu `cekLogin()`** di awal setiap fungsi yang butuh user login
5. **Loading state wajib** — tampilkan spinner saat query sedang jalan
6. **Jangan query berulang** — simpan data yang sudah diambil ke variabel, bukan query ulang
7. **Supabase ANON key aman** untuk ditaruh di HTML karena RLS yang menjaga keamanan data
8. **Tidak perlu backend server** — semua logika bisa di JavaScript langsung

---

*Arsitektur ini 100% gratis, 100% bisa dikerjakan sendiri di Zed, dan cukup untuk melayani ribuan pengguna Langit Korea.*
