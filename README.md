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

## 🧰 Tools Open Test EPS-TOPIK 2025

Tool ekstraksi resmi yang sudah berhasil dipakai ada di:

```bash
scripts/build_open_test_2025.py
```

Input yang dibutuhkan tetap berada di folder `downloads/`:

- `1. 읽기_공개 문항_20문항.pdf`
- `3. 듣기_공개 문항_20문항.pdf`
- `듣기문제 오디오 파일.zip`

Output yang dibuat:

- `open_test_2025.json`
- `assets/open-test/2025/images/*.png`
- `assets/open-test/2025/audio/q21.mp3` sampai `q40.mp3`

Command cepat:

```bash
npm run open-test:build
```

Untuk rebuild sekaligus update Supabase:

```bash
npm run open-test:upload
```

Jika menjalankan dari Windows PowerShell dan `npm.ps1` diblokir oleh execution policy, gunakan:

```powershell
npm.cmd run open-test:build
npm.cmd run open-test:upload
```

Catatan penting: paket PDF ini adalah Open Test tahun 2025. Teks header PDF tertulis `2025 - 253 - ...`, dan `simulasi.html` default memakai `year=2025`.

## Tools Modul Textbook 1 Unit 1-30

Tool build modul page-faithful textbook 1 ada di:

```bash
scripts/build_textbook1_modules.py
```

Input yang dipakai:

- `assets/EPS-TOPIK_textbook1 (1).zip`
- `assets/EPS-TOPIK_textbook1_listen (2).zip`

Output yang dibuat:

- `assets/modules/textbook1/index.json`
- `assets/modules/textbook1/unit_XX/source.pdf`
- `assets/modules/textbook1/unit_XX/module.json`
- `assets/modules/textbook1/unit_XX/pages/page_NN.jpg`
- `assets/modules/textbook1/audio/unit_XX/track_NNN.mp3`
- `assets/modules/textbook1/preliminary/audio/track_NNN.mp3`

Command cepat:

```bash
npm run modules:textbook1:build
```

Untuk render ulang semua PDF unit, halaman JPG, dan audio dari ZIP asli:

```bash
npm run modules:textbook1:force
```

Hasil saat ini: 30 unit textbook 1 sudah terbangun untuk unit 1-30. Setiap unit memiliki 10 gambar halaman asli, 1 PDF unit hasil potong dari PDF resmi, dan 5 audio unit. Audio pra-unit Track 001-027 juga disalin ke `assets/modules/textbook1/preliminary/audio/`.

## Tools Modul Textbook 2 Unit 31-60

Tool build modul page-faithful ada di:

```bash
scripts/build_textbook2_modules.py
```

Input yang dipakai:

- `assets/langit-korea-modules/unit_31..60*.pdf`
- `assets/langit-korea-modules/manifest.json`
- `assets/langit-korea-extracted/unit_31..60/reading_data.json`
- `assets/langit-korea-extracted/unit_31..60/listening_data.json`
- `data/unit_31.json` sampai `data/unit_60.json`
- `scripts/extracted_mp3/unit_XX_listening_N.mp3`

Output yang dibuat:

- `assets/modules/textbook2/index.json`
- `assets/modules/textbook2/unit_XX/module.json`
- `assets/modules/textbook2/unit_XX/pages/page_NN.jpg`
- `assets/modules/textbook2/audio/unit_XX/listening_N.mp3`

Command cepat:

```bash
npm run modules:textbook2:build
```

Untuk render ulang semua halaman JPG dari PDF asli:

```bash
npm run modules:textbook2:force
```

Hasil saat ini: 30 unit textbook 2 sudah terbangun untuk unit 31-60. Setiap unit memiliki 10 gambar halaman asli, 5 soal reading, 5 soal listening, dan 5 audio listening lokal.

## Tools Special EPS-TOPIK Work Related

Special EPS-TOPIK `Work related questions` adalah sumber terpisah dari textbook 1/2, jadi tidak digabung ke modul unit. Tool build-nya ada di:

```bash
scripts/build_special_eps_work.py
```

Input resmi diambil dari halaman HRD Korea:

- `https://epstopik.hrdkorea.or.kr/epstopik/book/pub/publicWorkBookList.do?lang=en`
- 8 PDF sektor kerja dari `https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/`
- `answersinSpecialEPSTOPIK.zip`

Output yang dibuat:

- `assets/special-eps/work-related/index.json`
- `assets/special-eps/work-related/sources/*.pdf`
- `assets/special-eps/work-related/<category>/module.json`
- `assets/special-eps/work-related/<category>/pages/page_NN.jpg`
- `assets/special-eps/work-related/answers/*.xlsx`

Command cepat:

```bash
npm run special-eps:work:build
```

Untuk download dan render ulang dari sumber resmi:

```bash
npm run special-eps:work:force
```

Hasil saat ini: 8 kategori Special EPS work-related sudah terbangun, total 300 halaman PDF-render dan 1.600 kunci jawaban dari XLSX resmi.

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
