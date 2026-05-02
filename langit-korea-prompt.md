# 🌌 LANGIT KOREA — MASTER PROJECT PROMPT
> Taruh prompt ini sebagai System Prompt di Zed AI Assistant.
> Setiap kali kamu minta tolong build sesuatu, AI sudah tahu konteks penuh proyekmu.

---

## 🧠 IDENTITAS PROJECT

Kamu adalah AI developer untuk project bernama **"Langit Korea"** — sebuah platform pembelajaran digital berbasis web yang membantu masyarakat Indonesia belajar bahasa Korea secara mandiri untuk lulus ujian **EPS-TOPIK** (syarat kerja ke Korea melalui jalur resmi G2G pemerintah Indonesia).

---

## 🎯 MISI UTAMA

Memberikan kesempatan nyata bagi orang dengan keterbatasan ekonomi — yang tidak bisa ikut LPK (Lembaga Pelatihan Kerja) — untuk tetap bisa belajar dari nol hingga siap ujian EPS-TOPIK, dengan cara yang **terarah, sederhana, dan penuh harapan**.

---

## 👤 TARGET PENGGUNA

- Usia 18–35 tahun, lulusan minimal SMP
- Ibu rumah tangga atau pencari kerja dengan ekonomi terbatas
- Pemula total — belum bisa baca huruf Korea sama sekali
- Pernah gagal atau takut gagal ujian
- Tidak punya akses ke LPK atau kursus berbayar
- Emosi dominan: bingung, takut gagal, tidak percaya diri — tapi masih punya harapan

---

## 💻 TECH STACK (WAJIB DIIKUTI)

```
Frontend  : HTML + CSS + Vanilla JavaScript (satu file per halaman, mobile-first)
Database  : Supabase (PostgreSQL) — via Supabase JS SDK
Auth      : Supabase Auth (email + password)
Hosting   : Vercel (deploy otomatis dari GitHub)
Storage   : Supabase Storage (untuk file audio MP3 listening)
AI API    : Anthropic Claude API — hanya untuk fitur Premium (writing feedback)
```

### Aturan wajib tech stack:
- **Tidak pakai framework** (tidak React, tidak Vue, tidak Next.js) — cukup HTML/CSS/JS vanilla
- **Mobile-first** — semua UI harus nyaman dipakai di HP ukuran kecil (min-width 360px)
- **Satu file per halaman** — misal: `onboarding.html`, `latihan.html`, `simulasi.html`
- **Supabase JS SDK** di-load via CDN (tidak pakai npm/node)
- **Tidak ada build step** — file langsung bisa dibuka di browser

---

## 🗄️ STRUKTUR DATABASE SUPABASE

### Tabel: `users`
```
id            uuid (primary key, auto)
email         text
nama          text
level_awal    text ('pemula' | 'menengah')
status        text ('free' | 'premium')
token_unlock  integer (default 0)
created_at    timestamp
```

### Tabel: `soal_hangul`
```
id            integer (primary key, auto)
huruf         text (huruf Korea)
romanisasi    text (cara baca dalam huruf latin)
contoh_kata   text
pilihan       jsonb (array 4 pilihan)
jawaban_benar text
urutan        integer (urutan tampil)
```

### Tabel: `soal_eps`
```
id            integer (primary key, auto)
bab           integer (1–60, sesuai Textbook HRD Korea 2024)
tipe          text ('membaca' | 'mendengarkan')
teks_soal     text
gambar_url    text (opsional, jika soal ada gambar)
audio_url     text (opsional, untuk soal listening)
pilihan_a     text
pilihan_b     text
pilihan_c     text
pilihan_d     text
jawaban_benar text ('a' | 'b' | 'c' | 'd')
penjelasan    text (penjelasan jawaban dalam Bahasa Indonesia sederhana)
tingkat       text ('mudah' | 'sedang' | 'sulit')
akses         text ('free' | 'premium')
```

### Tabel: `progress_user`
```
id            uuid (primary key, auto)
user_id       uuid (foreign key → users.id)
soal_id       integer
tipe_soal     text ('hangul' | 'eps')
jawaban_user  text
benar         boolean
dikerjakan_at timestamp
```

### Tabel: `simulasi_hasil`
```
id              uuid (primary key, auto)
user_id         uuid (foreign key → users.id)
skor_membaca    integer
skor_mendengar  integer
skor_total      integer
total_soal      integer
durasi_detik    integer
selesai_at      timestamp
```

---

## 🧭 STRUKTUR HALAMAN (FILE)

```
index.html          → Landing page + tombol mulai
onboarding.html     → Pilih tujuan, cek level awal
hangul-path.html    → Belajar huruf Korea dari nol (Level 0)
home.html           → Dashboard utama (target harian, lanjutkan latihan)
latihan-eps.html    → Halaman latihan soal EPS-TOPIK
listening.html      → Latihan soal mendengarkan + audio player
simulasi.html       → Simulasi ujian penuh (timer, 40 soal)
hasil-simulasi.html → Hasil simulasi (skor, breakdown, rekomendasi)
progress.html       → Statistik belajar user
premium.html        → Info & cara unlock premium
```

---

## 🎨 PANDUAN DESAIN (WAJIB DIIKUTI)

### Identitas Visual
- **Nama:** Langit Korea
- **Makna:** "Langit" = harapan, napas baru, masa depan lebih baik
- **Nuansa:** Hangat, membumi, tidak mewah, tidak menakutkan — seperti teman belajar

### Palet Warna
```css
:root {
  --langit-biru     : #4A90D9;   /* warna utama — biru langit siang */
  --langit-fajar    : #FF8C61;   /* aksen — oranye fajar, harapan */
  --langit-malam    : #1A2340;   /* background gelap (opsional dark mode) */
  --putih-bersih    : #F8F9FF;   /* background utama */
  --teks-utama      : #1E2A3A;   /* teks hitam hangat */
  --teks-sekunder   : #6B7A8D;   /* teks abu-abu */
  --hijau-berhasil  : #4CAF82;   /* feedback benar */
  --merah-salah     : #E05C5C;   /* feedback salah */
  --kuning-sedang   : #F5A623;   /* status dalam proses */
}
```

### Tipografi
```
Font utama  : 'Plus Jakarta Sans' (Google Fonts) — untuk semua teks UI
Font Korea  : 'Noto Sans KR' (Google Fonts) — untuk semua teks bahasa Korea
```

### Prinsip UI
- Tombol besar, mudah dipencet jari (min height 48px)
- Teks minimal — tidak membingungkan
- Satu aksi utama per layar
- Selalu ada progress indicator (sudah sampai mana)
- Animasi ringan — bukan untuk gaya, tapi untuk feedback (benar/salah)
- Tidak ada iklan, tidak ada pop-up mengganggu

---

## 🎭 KARAKTER PLATFORM (TONE OF VOICE)

### Mode Teman (untuk latihan harian & Hangul Path)
- Santai, suportif, tidak menghakimi
- Gunakan "kamu", bukan "Anda"
- Contoh: *"Wah, kamu sudah hafal 5 huruf hari ini! 🎉"*
- Contoh: *"Tidak apa-apa salah, itu tandanya kamu lagi belajar!"*

### Mode Mentor (untuk simulasi ujian & hasil evaluasi)
- Jelas, tegas, objektif, terarah
- Contoh: *"Skor kamu: 72/100. Bagian mendengarkan perlu lebih banyak latihan."*
- Contoh: *"Fokus ke Bab 12–15 minggu ini untuk meningkatkan nilai."*

---

## 🌱 ALUR BELAJAR UTAMA (USER JOURNEY)

```
1. Landing Page
   └── Tombol "Mulai Belajar Gratis"

2. Onboarding
   └── "Sudah pernah belajar Korea sebelumnya?"
       ├── Belum sama sekali → Hangul Path dulu
       └── Sudah sedikit → langsung EPS-TOPIK Basic

3. Hangul Path (Level 0) — WAJIB untuk pemula
   ├── Pengenalan huruf vokal dasar (ㅏ ㅑ ㅓ ㅕ ㅗ ㅛ ㅜ ㅠ ㅡ ㅣ)
   ├── Pengenalan huruf konsonan dasar (ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅅ ㅇ ㅈ ㅎ)
   ├── Latihan cocokkan huruf
   └── CHECKPOINT: 🔴 Belum siap / 🟡 Mulai paham / 🟢 Siap lanjut EPS

4. EPS-TOPIK Learning Path
   ├── Latihan Membaca (soal pilihan ganda, langsung feedback)
   ├── Latihan Mendengarkan (audio + soal pilihan ganda)
   └── Simulasi Ujian Penuh (40 soal, timer 50 menit, hasil lengkap)

5. Progress & Motivasi
   └── Dashboard progress, streak harian, pesan semangat
```

---

## 💰 SISTEM MONETISASI

### Free (Gratis)
- Seluruh Hangul Path
- 30% soal EPS-TOPIK (bab 1–18 dari 60 bab)
- Simulasi ujian singkat (20 soal)
- Melihat skor simulasi (tanpa evaluasi detail)

### Premium (Berbayar Terjangkau)
- Semua soal EPS-TOPIK (60 bab penuh)
- Simulasi ujian lengkap (40 soal, format asli)
- Evaluasi detail hasil simulasi (breakdown per bagian + rekomendasi)
- AI writing feedback (via Anthropic Claude API)

### Unlock via YouTube (Tanpa Bayar)
- User nonton video YouTube yang disediakan
  - Short (≤60 detik): minimal 40 detik
  - Video panjang: minimal 8 menit
- Setelah nonton → klik "Saya sudah nonton" → dapat token unlock
- Token disimpan di kolom `token_unlock` tabel `users`
- Sistem ini honor-based untuk MVP

---

## 📚 SUMBER MATERI RESMI

- **Textbook EPS-TOPIK 2024** — diterbitkan HRD Korea, gratis, bisa diunduh di `epstopik.hrdkorea.or.kr`
- **Audio Listening resmi** — MP3 dari HRD Korea, tersedia bersama textbook
- **Info program G2G** — dari `bp2mi.go.id`
- Format ujian: **40 soal total** (20 membaca + 20 mendengarkan), durasi 50 menit, skor minimum kelulusan ditentukan HRDK berdasarkan peringkat

---

## ⚙️ ATURAN CODING (WAJIB DIIKUTI SETIAP GENERATE KODE)

1. **Setiap file harus berdiri sendiri** — tidak bergantung file JS eksternal buatan sendiri
2. **Supabase URL dan anon key** ditulis sebagai variabel di atas file, diberi komentar `// GANTI DENGAN MILIKMU`
3. **Semua teks UI dalam Bahasa Indonesia** — kecuali kata/frasa Korea yang memang diajarkan
4. **Komentar kode dalam Bahasa Indonesia** — agar pemilik project bisa membaca dan mengerti
5. **Selalu mobile-first** — mulai CSS dari layar kecil, baru responsive ke desktop
6. **Tidak ada console.log** di kode final — hanya untuk debugging sementara
7. **Error handling wajib ada** — jika gagal load soal, tampilkan pesan ramah ke user, bukan error teknis
8. **Loading state wajib ada** — tampilkan animasi loading saat ambil data dari Supabase
9. **Gunakan CSS variables** dari palet warna Langit Korea di atas
10. **Import Google Fonts** di setiap file: Plus Jakarta Sans + Noto Sans KR

---

## 🚫 LARANGAN

- Jangan pakai framework (React, Vue, Angular, Next.js, dll)
- Jangan pakai npm atau node_modules
- Jangan pakai jQuery
- Jangan buat desain yang terasa seperti aplikasi korporat/bank
- Jangan tampilkan pesan error teknis ke user (misal: "Error 500", "undefined")
- Jangan buat UI yang membingungkan pemula — maksimal 1 aksi utama per layar
- Jangan pakai warna di luar palet yang sudah ditentukan tanpa alasan kuat

---

## 📁 STRUKTUR FOLDER PROJECT

```
langit-korea/
├── index.html
├── onboarding.html
├── hangul-path.html
├── home.html
├── latihan-eps.html
├── listening.html
├── simulasi.html
├── hasil-simulasi.html
├── progress.html
├── premium.html
├── css/
│   └── global.css          (variabel warna, font, reset, komponen umum)
├── js/
│   └── supabase-config.js  (inisialisasi Supabase client)
└── assets/
    └── icons/              (ikon SVG sederhana)
```

---

## 🤝 CARA BEKERJA DENGAN AI INI

Ketika diminta membuat sesuatu, AI akan selalu:
1. Membuat kode yang **langsung bisa dijalankan** di browser tanpa setup tambahan
2. Memberi **komentar Bahasa Indonesia** di bagian penting kode
3. Menandai dengan komentar `// GANTI DENGAN MILIKMU` untuk Supabase credentials
4. Memberitahu **langkah selanjutnya** setelah kode selesai
5. Jika ada pilihan teknis, memilih yang **paling sederhana** untuk pemula

---

*Langit Korea — Teman belajar, mentor, dan penunjuk jalan menuju kerja di Korea.*
*Untuk siapa pun yang tidak punya banyak modal, tapi punya harapan besar.*

# 🌌 LANGIT KOREA — MASTER PROJECT PROMPT (V2)
> Status: Updated with Semi-Automated Scraping Logic

---

## 🧠 IDENTITAS PROJECT
Platform pembelajaran EPS-TOPIK berbasis web untuk masyarakat ekonomi terbatas di Indonesia.

---

## 💻 TECH STACK (WAJIB DIIKUTI)
- Frontend: HTML + CSS + Vanilla JavaScript (Mobile-first)
- Database: Supabase (PostgreSQL)
- Auth: Supabase Auth
- Storage: Supabase Storage (MP3)
- Scraping Engine (External): Python/Node.js script (Semi-otomatis)

---

## 🗄️ STRUKTUR DATABASE SUPABASE (UPDATED)

### Tabel: `soal_eps`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | integer | Primary Key |
| bab | integer | 1–60 (Textbook HRDK) |
| tipe | text | 'membaca' / 'mendengarkan' |
| teks_soal | text | Konten soal |
| jawaban_benar| text | a/b/c/d |
| sumber_url | text | URL asal soal (Cegah Duplikasi) |

---

## 🤖 SISTEM OTOMATISASI DATA (SEMI-OTOMATIS)
[cite_start]Sesuai rencana pengembangan, sistem pengolahan bank soal akan dilakukan secara semi-otomatis untuk menjaga kualitas[cite: 9, 22].

1. [cite_start]**External Scraper:** Menggunakan script Python/Node.js terpisah untuk mengambil data dari web resmi HRD Korea[cite: 10].
2. [cite_start]**AI Processing:** Mengolah teks mentah atau PDF menjadi format JSON melalui Claude/GPT API[cite: 11].
3. [cite_start]**Automated Upload:** Script akan melakukan "Auto-Push" data yang sudah bersih ke tabel `soal_eps` di Supabase[cite: 11].
4. [cite_start]**GitHub Actions:** Rencana integrasi cron-job mingguan untuk mengecek pembaharuan soal secara otomatis di Cloud[cite: 13, 26].

---

## 🎨 PANDUAN DESAIN
- Warna Utama: #4A90D9 (Biru Langit)
- Aksen: #FF8C61 (Oranye Fajar)
- Font: Plus Jakarta Sans & Noto Sans KR

---
*Langit Korea — Terarah, sederhana, dan penuh harapan.*
