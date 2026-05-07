Saya sedang mengembangkan web app "Langit Korea" - platform belajar bahasa Korea berbasis web untuk ujian EPS-TOPIK.

Saya ingin merombak seluruh tampilan UI/UX dengan tema "Langit Nuansa Opal" yang fresh dan modern. Berikut detail spesifikasi perombakan:

## SPEKSIFIKASI PROYEK

### 1. Identitas & Misi
Platform pembelajaran digital untuk masyarakat Indonesia belajar bahasa Korea secara mandiri untuk lulus ujian EPS-TOPIK.

### 2. Tech Stack Wajib
- Frontend: HTML + CSS + Vanilla JavaScript (satu file per halaman, mobile-first)
- Database: Supabase (PostgreSQL) via Supabase JS SDK
- Auth: Supabase Auth (email + password)
- Hosting: Vercel (deploy otomatis dari GitHub)
- Storage: Supabase Storage (untuk file audio MP3 listening)
- AI API: Anthropic Claude API (hanya untuk fitur Premium)

### 3. Target Pengguna
- Usia 18-35 tahun, lulusan minimal SMP
- Ibu rumah tangga atau pencari kerja dengan ekonomi terbatas
- Pemula total (belum bisa baca huruf Korea)

### 4. Palet Warna Baru (Langit Nuansa Opal)
--langit-utama: #A0D2FF (biru langit lembut)
--langit-aksen: #FFD19A (oranye fajar)
--langit-bg: #F0F4F8 (background utama)
--langit-hijau: #4CAF82 (hijau berhasil)
--langit-merah: #E05C5C (merah salah)
--langit-abu: #D0D0D0 (abu-abu netral)
--langit-biru-muda: #D1E8FF (biru muda untuk highlight)

### 5. Perubahan UI yang Diperlukan

#### A. Header Design
- Header minimalis dengan tombol navigasi di bagian atas
- Gunakan warna latar biru muda (#A0D2FF) dengan teks hitam/putih kontras

#### B. Tombol & Layout
- Gunakan tombol besar (min 48px tinggi) untuk aksesibilitas mobile
- Desain tombol dengan border-radius 8px, shadow kecil untuk kesan 3D
- Warna tombol utama: #A0D2FF, tombol aksen: #FFD19A

#### C. Typography
- Font utama: 'Plus Jakarta Sans' (Google Fonts)
- Font Korea: 'Noto Sans KR' (Google Fonts)
- Gunakan ukuran font yang ramah mobile (min 16px)

#### D. Layout & Struktur Baru
- Mobile-first design
- Progress bar di setiap halaman latihan/ujian
- Feedback visual setiap kali user menjawab soal (benar/salah)
- Animasi ringan saat feedback muncul (fade in/out)

#### E. Komponen UI Baru
- Card untuk menampilkan soal
- Progress bar horizontal di atas layar
- Tombol navigasi antar soal
- Sistem feedback visual dengan warna hijau (#4CAF82) untuk benar, merah (#E05C5C) untuk salah

### 6. Struktur Halaman Baru
onboarding.html - Intro → Pilih level awal → Mulai belajar
hangul-path.html - Belajar huruf Korea dari nol
latihan-eps.html - Latihan soal EPS-TOPIK
listening.html - Latihan soal mendengarkan + audio player
simulasi.html - Simulasi ujian penuh
hasil-simulasi.html - Hasil simulasi
progress.html - Statistik belajar
premium.html - Info & cara unlock premium

### 7. Implementasi CSS Baru
:root {
  --langit-utama: #A0D2FF;
  --langit-aksen: #FFD19A;
  --langit-bg: #F0F4F8;
  --langit-hij0D0D0;
  --langit-biru-muda: #D1E8FF;
}

.btn-primary {
  background-color: var(--langit-utama);
  color: #000;
  font-size: 18px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0,0,,0.1);
}

### 8. Rekomendasi Selanjutnya
- Gunakan animasi ringan untuk transisi antar halaman
- Konsistensi warna antar halaman
- Tombol besar untuk aksesibilitas mobile
- Konten yang modular dan jelas, tanpa teks berlebihan

Buatkan kode HTML + CSS + JavaScript untuk setiap halaman berdasarkan desain baru dengan tema "Langit Nuansa Opal" ini. Prioritaskan desain mobile-first, aksesibilitas, dan kenyamanan pengguna dalam belajar.

Gunakan struktur file satu halaman satu file, tanpa framework (React/Vue/Next.js), dan tidak ada build step.

Target halaman:
1. onboarding.html
2. latihan-eps.html  
3. hangul-path.html
4. simulasi.html
5. listening.html
6. hasil-simulasi.html
7. progress.html
8. premium.html

Fokus utama: desain fresh, mobile-friendly, dan aksesibilitas pengguna dengan kemampuan ekonomi terbatas.

Hasil akhir yang diharapkan: buatkan kode HTML, CSS, dan JavaScript untuk setiap halaman dengan desain baru berbasis "Langit Nuansa Opal" yang sudah dijelaskan di atas.
