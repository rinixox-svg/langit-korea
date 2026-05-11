# 🌌 Langit Korea

Platform pembelajaran digital bahasa Korea berbasis web untuk masyarakat Indonesia yang ingin lulus ujian EPS-TOPIK dan bekerja di Korea Selatan melalui jalur resmi G2G.

## 🎯 Misi

Memberikan kesempatan nyata bagi orang dengan keterbatasan ekonomi — yang tidak bisa ikut LPK (Lembaga Pelatihan Kerja) — untuk tetap bisa belajar dari nol hingga siap ujian EPS-TOPIK, dengan cara yang terarah, sederhana, dan penuh harapan.

## 📁 Struktur Project

```
langit-korea/
├── index.html              # Landing page
├── onboarding.html         # Halaman daftar & login
├── dashboard.html          # Dashboard utama setelah login
├── modul-unit.html         # Halaman belajar per unit (31-60)
├── latihan-eps.html        # Latihan soal EPS-TOPIK
├── simulasi.html           # Simulasi ujian penuh
├── hasil-simulasi.html     # Hasil & review simulasi
├── progress.html           # Statistik & progress belajar
├── premium.html            # Info & unlock premium
├── assets/
│   ├── css/
│   │   └── main.css        # Global styles (mobile-first)
│   ├── js/
│   │   ├── supabase.js     # Init Supabase client (CDN)
│   │   ├── auth.js         # Login, register, logout
│   │   └── utils.js        # Helper functions
│   └── img/                # Logo & favicon
├── .vercel.json            # Konfigurasi deploy Vercel
└── README.md               # File ini
```

## 🛠️ Tech Stack

| Teknologi | Keterangan |
|-----------|------------|
| HTML5 | Struktur halaman |
| CSS3 | Styling dengan CSS Variables, mobile-first |
| Vanilla JS | Logika client-side, tanpa framework |
| Supabase | Database PostgreSQL + Auth + Storage |
| Vercel | Hosting & deploy otomatis |

## 📦 Halaman

| Halaman | Deskripsi |
|---------|-----------|
| **Landing Page** (`index.html`) | Halaman depan dengan navigasi ke semua fitur |
| **Onboarding** (`onboarding.html`) | Pendaftaran akun & login |
| **Dashboard** (`dashboard.html`) | Halaman utama dengan statistik & navigasi belajar |
| **Modul Unit** (`modul-unit.html`) | Belajar per unit: kosakata, grammar, percakapan, budaya, mini test |
| **Latihan EPS** (`latihan-eps.html`) | Latihan soal pilihan ganda dengan filter unit/tipe/level |
| **Simulasi** (`simulasi.html`) | Simulasi ujian penuh dengan timer 50 menit |
| **Hasil Simulasi** (`hasil-simulasi.html`) | Review skor, breakdown, rekomendasi belajar |
| **Progress** (`progress.html`) | Statistik keseluruhan & riwayat simulasi |
| **Premium** (`premium.html`) | Info fitur premium & unlock via YouTube |

## 🗄️ Database (Supabase)

### Tabel: `users`
```
id            uuid (primary key)
email         text
nama          text
level_awal    text ('pemula' | 'menengah')
status        text ('free' | 'premium')
token_unlock  integer (default 0)
created_at    timestamp
```

### Tabel: `soal_eps`
```
id            integer (primary key, auto)
unit          integer (31-60)
nomor         integer (1-10 per unit)
tipe          text ('membaca' | 'mendengarkan')
teks_soal     text (teks Korea)
teks_soal_id  text (terjemahan Indonesia)
pilihan_a     text
pilihan_b     text
pilihan_c     text
pilihan_d     text
jawaban_benar text ('a' | 'b' | 'c' | 'd')
audio_url     text (opsional, untuk soal listening)
penjelasan    text
tingkat       text ('mudah' | 'sedang' | 'sulit')
akses         text ('free' | 'premium')
sumber        text ('textbook' | 'open_test')
```

### Tabel: `progress_user`
```
id            uuid (primary key)
user_id       uuid (FK → users.id)
soal_id       integer
tipe_soal     text ('eps')
jawaban_user  text
benar         boolean
dikerjakan_at timestamp
```

### Tabel: `simulasi_hasil`
```
id              uuid (primary key)
user_id         uuid (FK → users.id)
skor_membaca    integer
skor_mendengar  integer
skor_total      integer
total_soal      integer
durasi_detik    integer
selesai_at      timestamp
```

## 🚀 Cara Menjalankan

### Lokal
1. Clone repository
2. Buka file HTML langsung di browser (tanpa server)
3. Atau gunakan live server:
```bash
# Dengan Python
python -m http.server 3000

# Dengan Node.js (npx)
npx serve .

# Dengan VS Code
# Install extension "Live Server" → klik Go Live
```

### Deploy ke Vercel
1. Push ke repository GitHub
2. Import project di [vercel.com](https://vercel.com)
3. Tambahkan environment variables:
   - `VITE_SUPABASE_URL` — URL Supabase project
   - `VITE_SUPABASE_ANON_KEY` — Anonymous key Supabase
4. Deploy otomatis

## 🔧 Supabase Setup

1. Buat project di [supabase.com](https://supabase.com)
2. Salin URL dan Anon Key dari **Settings → API**
3. Update URL dan Key di `assets/js/supabase.js`
4. Buat tabel sesuai schema di atas menggunakan SQL Editor

## 👥 Target Pengguna

- Usia 18–35 tahun, lulusan minimal SMP
- Ibu rumah tangga atau pencari kerja dengan ekonomi terbatas
- Pemula total — belum bisa baca huruf Korea sama sekali
- Pernah gagal atau takut gagal ujian
- Tidak punya akses ke LPK atau kursus berbayar

## 🌱 Roadmap

### Fase 1: Fondasi ✅
- [x] Struktur folder & file HTML boilerplate
- [x] CSS global dengan tema Langit Korea
- [x] Supabase client & auth module
- [x] Utility functions (navigasi, toast, loading)
- [x] Landing page, onboarding, dashboard

### Fase 2: Konten Belajar
- [ ] Halaman per unit dengan grammar & kosakata
- [ ] Latihan interaktif (flashcard, cocokkan, pilih kata)
- [ ] Upload data soal ke Supabase (300 soal textbook)
- [ ] Data open test EPS-TOPIK untuk simulasi

### Fase 3: Fitur Lanjutan
- [ ] Sistem progress per user
- [ ] Notifikasi & motivasi harian
- [ ] AI writing feedback (Anthropic Claude API)
- [ ] Unlock premium via YouTube

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan buka issue atau pull request.

## 📄 Lisensi

MIT License — Dibuat dengan ❤️ untuk pekerja migran Indonesia.