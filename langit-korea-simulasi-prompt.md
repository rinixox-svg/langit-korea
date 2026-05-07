# LANGIT KOREA — PROMPT SIMULASI UJIAN EPS-TOPIK
# Gunakan prompt ini di Zed untuk build 3 halaman:
# 1. briefing.html  → Pemberitahuan aturan ujian (Do's & Don'ts)
# 2. practice.html  → Latihan setengah (20 soal: 10 reading + 10 listening)
# 3. simulasi.html  → Simulasi penuh (40 soal: 20 reading + 20 listening)
#
# Gabungkan dengan langit-korea-prompt.md dan langit-korea-backend-prompt.md

---

## 🎯 KONTEKS

Ini adalah MVP utama Langit Korea. Simulasi harus:
1. IDENTIK dengan format ujian EPS-TOPIK asli (UBT/CBT HRD Korea)
2. Punya fitur khas Langit Korea yang tidak ada di ujian asli
3. Mobile-first, ramah pemula total
4. Mengambil soal dari Supabase (tabel soal_eps)

---

## 📋 FORMAT UJIAN ASLI (WAJIB DIIKUTI PERSIS)

### Spesifikasi resmi EPS-TOPIK (UBT 2024):
```
Total soal    : 40 soal
Reading       : Nomor 1–20 | 25 menit
Listening     : Nomor 21–40 | 25 menit
Total waktu   : 50 menit
Skor maks     : 200 poin (100 reading + 100 listening)
Nilai lulus   : ≥ 80 poin
Poin per soal : 5 poin (benar), 0 poin (salah, tidak dikurangi)
Semua pilihan : 4 opsi (①②③④)
Bahasa soal   : Korea SAJA — tidak ada terjemahan saat ujian
```

### Aturan LISTENING (wajib diikuti):
```
- Tombol PLAY ditekan manual oleh user
- Audio otomatis putar 2 KALI, tidak bisa diulang manual
- Saat audio berjalan: tombol Previous, Next, dan grid soal TERKUNCI
- Setelah audio selesai 2x: baru bisa lanjut/navigasi
```

### Tipe soal per nomor:
```
READING (1–20):
  No. 1–2   → soal_bergambar     : lihat gambar → pilih kata/kalimat
  No. 3–4   → sinonim_antonim    : pilih sinonim/antonim kata
  No. 5–8   → isi_kosong         : isi bagian kosong dalam kalimat
  No. 9–12  → baca_gambar        : baca teks dalam gambar, pilih benar/salah
  No. 13–14 → lengkapi_kalimat   : lengkapi kalimat (kosakata + grammar)
  No. 15–16 → bacaan_pendek      : baca pendek → pilih kata inti
  No. 17–20 → artikel_panjang    : baca artikel → pilih isi yang sesuai

LISTENING (21–40):
  No. 21–22 → dengar_jawab_teks  : dengar audio → pilih jawaban teks
  No. 23–24 → dengar_jawab_gambar: dengar audio → pilih jawaban bergambar
  No. 25–29 → dengar_pilih_gambar: dengar audio + lihat gambar → pilih
  No. 30–33 → dengar_pertanyaan  : dengar pertanyaan → pilih jawaban
  No. 34–35 → dengar_lanjutan    : dengar audio → pilih kalimat lanjutan
  No. 36–37 → dengar_topik       : tentukan topik percakapan
  No. 38–40 → dengar_cerita      : dengar cerita panjang → pilih yang benar
```

---

## 🗄️ CARA AMBIL SOAL DARI SUPABASE

### Query soal untuk PRACTICE (20 soal):
```javascript
async function ambilSoalPractice() {
    // 10 reading: ambil random dari soal membaca yang tersedia
    const { data: reading } = await db
        .from('soal_eps')
        .select('*')
        .eq('tipe', 'membaca')
        .eq('akses', 'free')
        .limit(40)  // ambil lebih banyak dulu untuk di-shuffle

    // 10 listening: ambil random dari soal mendengarkan
    const { data: listening } = await db
        .from('soal_eps')
        .select('*')
        .eq('tipe', 'mendengarkan')
        .eq('akses', 'free')
        .limit(40)

    // Shuffle dan ambil 10 masing-masing
    const readingShuffled = shuffle(reading).slice(0, 10)
    const listeningShuffled = shuffle(listening).slice(0, 10)

    // Gabung: reading nomor 1-10, listening nomor 11-20
    return [
        ...readingShuffled.map((s, i) => ({ ...s, nomor_tampil: i + 1 })),
        ...listeningShuffled.map((s, i) => ({ ...s, nomor_tampil: i + 11 }))
    ]
}
```

### Query soal untuk SIMULASI PENUH (40 soal):
```javascript
async function ambilSoalSimulasi() {
    // Ambil pool soal yang cukup besar
    const { data: reading } = await db
        .from('soal_eps')
        .select('*')
        .eq('tipe', 'membaca')
        .limit(100)

    const { data: listening } = await db
        .from('soal_eps')
        .select('*')
        .eq('tipe', 'mendengarkan')
        .limit(100)

    // Distribusi sesuai tipe soal ujian asli
    const soalTerpilih = distribusiSoalUjian(reading, listening)

    return soalTerpilih
}

// Pilah soal berdasarkan field 'tipe_soal_ujian' dari database
// Field ini perlu ditambahkan ke tabel soal_eps:
// tipe_soal_ujian: 'soal_bergambar'|'sinonim_antonim'|'isi_kosong'|...

function distribusiSoalUjian(readingPool, listeningPool) {
    const hasil = []
    let nomor = 1

    // Reading: distribusikan per tipe
    const distribusiReading = [
        { tipe: 'soal_bergambar',  jumlah: 2 },  // No. 1-2
        { tipe: 'sinonim_antonim', jumlah: 2 },  // No. 3-4
        { tipe: 'isi_kosong',      jumlah: 4 },  // No. 5-8
        { tipe: 'baca_gambar',     jumlah: 4 },  // No. 9-12
        { tipe: 'lengkapi_kalimat',jumlah: 2 },  // No. 13-14
        { tipe: 'bacaan_pendek',   jumlah: 2 },  // No. 15-16
        { tipe: 'artikel_panjang', jumlah: 4 },  // No. 17-20
    ]

    const distribusiListening = [
        { tipe: 'dengar_jawab_teks',   jumlah: 2 },  // No. 21-22
        { tipe: 'dengar_jawab_gambar', jumlah: 2 },  // No. 23-24
        { tipe: 'dengar_pilih_gambar', jumlah: 5 },  // No. 25-29
        { tipe: 'dengar_pertanyaan',   jumlah: 4 },  // No. 30-33
        { tipe: 'dengar_lanjutan',     jumlah: 2 },  // No. 34-35
        { tipe: 'dengar_topik',        jumlah: 2 },  // No. 36-37
        { tipe: 'dengar_cerita',       jumlah: 3 },  // No. 38-40
    ]

    for (const { tipe, jumlah } of distribusiReading) {
        const pool = readingPool.filter(s => s.tipe_soal_ujian === tipe)
        const dipilih = shuffle(pool).slice(0, jumlah)
        dipilih.forEach(s => hasil.push({ ...s, nomor_tampil: nomor++ }))
    }

    for (const { tipe, jumlah } of distribusiListening) {
        const pool = listeningPool.filter(s => s.tipe_soal_ujian === tipe)
        const dipilih = shuffle(pool).slice(0, jumlah)
        dipilih.forEach(s => hasil.push({ ...s, nomor_tampil: nomor++ }))
    }

    return hasil
}

function shuffle(arr) {
    if (!arr) return []
    const a = [...arr]
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]]
    }
    return a
}
```

### Tambahan kolom di tabel soal_eps (jalankan di Supabase SQL):
```sql
-- Tambah kolom tipe_soal_ujian untuk distribusi
ALTER TABLE public.soal_eps
ADD COLUMN IF NOT EXISTS tipe_soal_ujian text
CHECK (tipe_soal_ujian IN (
    'soal_bergambar', 'sinonim_antonim', 'isi_kosong', 'baca_gambar',
    'lengkapi_kalimat', 'bacaan_pendek', 'artikel_panjang',
    'dengar_jawab_teks', 'dengar_jawab_gambar', 'dengar_pilih_gambar',
    'dengar_pertanyaan', 'dengar_lanjutan', 'dengar_topik', 'dengar_cerita'
));

-- Update soal unit 31 berdasarkan pemetaan yang sudah ada
UPDATE soal_eps SET tipe_soal_ujian = 'sinonim_antonim'    WHERE unit=31 AND tipe='membaca' AND nomor=1;
UPDATE soal_eps SET tipe_soal_ujian = 'lengkapi_kalimat'   WHERE unit=31 AND tipe='membaca' AND nomor=2;
UPDATE soal_eps SET tipe_soal_ujian = 'isi_kosong'         WHERE unit=31 AND tipe='membaca' AND nomor=3;
UPDATE soal_eps SET tipe_soal_ujian = 'isi_kosong'         WHERE unit=31 AND tipe='membaca' AND nomor=4;
UPDATE soal_eps SET tipe_soal_ujian = 'artikel_panjang'    WHERE unit=31 AND tipe='membaca' AND nomor=5;
UPDATE soal_eps SET tipe_soal_ujian = 'dengar_jawab_gambar' WHERE unit=31 AND tipe='mendengarkan' AND nomor=1;
UPDATE soal_eps SET tipe_soal_ujian = 'dengar_jawab_teks'  WHERE unit=31 AND tipe='mendengarkan' AND nomor=2;
UPDATE soal_eps SET tipe_soal_ujian = 'dengar_topik'       WHERE unit=31 AND tipe='mendengarkan' AND nomor=3;
UPDATE soal_eps SET tipe_soal_ujian = 'dengar_lanjutan'    WHERE unit=31 AND tipe='mendengarkan' AND nomor=4;
UPDATE soal_eps SET tipe_soal_ujian = 'dengar_cerita'      WHERE unit=31 AND tipe='mendengarkan' AND nomor=5;
```

---

## 🎨 DESAIN VISUAL (IDENTITAS LANGIT KOREA)

```css
/* Warna — dari global.css Langit Korea */
--langit-biru    : #4A90D9;
--langit-fajar   : #FF8C61;
--putih-bersih   : #F8F9FF;
--teks-utama     : #1E2A3A;
--teks-sekunder  : #6B7A8D;
--hijau-berhasil : #4CAF82;
--merah-salah    : #E05C5C;
--kuning-sedang  : #F5A623;

/* Font */
/* Plus Jakarta Sans + Noto Sans KR via Google Fonts */
```

### State warna grid soal:
```
□ Abu-abu terang  → belum dijawab
■ Biru #4A90D9    → sudah dijawab
▣ Oranye #FF8C61  → soal aktif sekarang
🔒 Terkunci       → saat audio listening berjalan
```

---

## 🏗️ HALAMAN 1: `briefing.html` (Pemberitahuan Sebelum Ujian)

### Fungsi:
Halaman ini muncul SEBELUM ujian/practice dimulai. User WAJIB baca sebelum mulai.

### Konten (2 tab: Practice dan Simulasi):
```
Tab Practice (20 soal):
- Durasi: 25 menit
- 10 soal reading + 10 soal listening
- Bisa review jawaban setelah selesai ✅
- Penjelasan jawaban tersedia ✅

Tab Simulasi (40 soal):
- Durasi: 50 menit
- 20 soal reading + 20 soal listening
- Format identik ujian asli
- Review hanya untuk premium ⭐
```

### Do's & Don'ts (berlaku untuk keduanya):
```
✅ DO:
- Pastikan volume HP/laptop menyala untuk listening
- Pakai headset jika memungkinkan
- Jawab semua soal meski tidak yakin (tidak ada pengurangan poin)
- Bisa loncat soal dan kembali lagi (kecuali saat audio berjalan)
- Sisa waktu tersedia di sudut kanan atas

🚫 DON'T:
- Jangan tutup atau refresh halaman saat ujian berjalan
- Jangan putar ulang audio listening (hanya putar 2x otomatis)
- Jangan tinggalkan halaman saat timer berjalan
- Jangan klik di luar soal saat audio sedang berjalan
```

### UI notes:
- Tombol "Mulai" disabled 3 detik pertama → dorong user baca dulu
- Countdown kecil "Tombol aktif dalam 3..." → "Siap? Mulai Sekarang"
- Tone: Mode Teman — santai, tidak menakutkan

---

## 🏗️ HALAMAN 2: `practice.html` (Latihan Setengah)

### Spesifikasi:
```
Total soal : 20 (10 reading + 10 listening)
Durasi     : 25 menit (hitung mundur)
Nomor      : Reading 1–10, Listening 11–20
Skor maks  : 100 poin (50 reading + 50 listening)
Nilai lulus: ≥ 40 poin
Akses      : Free
```

### Fitur khas Langit Korea di Practice:
- Review jawaban setelah selesai ✅
- Penjelasan jawaban dalam Bahasa Indonesia ✅ (premium)
- Skor ditampilkan dengan pesan motivasi
- Bisa lihat mana yang benar/salah ✅

---

## 🏗️ HALAMAN 3: `simulasi.html` (Simulasi Penuh)

### Spesifikasi:
```
Total soal : 40 (20 reading + 20 listening)
Durasi     : 50 menit (hitung mundur)
Nomor      : Reading 1–20, Listening 21–40
Skor maks  : 200 poin
Nilai lulus: ≥ 80 poin
Akses      : Free (soal) + Premium (review+penjelasan)
```

### Fitur khas Langit Korea di Simulasi:
- Status kesiapan setelah selesai (bukan hanya lulus/tidak)
- Analisa kelemahan per tipe soal
- Rekomendasi unit untuk dipelajari ulang
- Review premium: lihat penjelasan per soal

---

## 💻 KODE LENGKAP

### Minta AI Zed generate file ini satu per satu:

```
Request 1: Buat briefing.html
Request 2: Buat practice.html
Request 3: Buat simulasi.html
Request 4: Buat hasil-simulasi.html (halaman hasil)
```

---

### TEMPLATE STRUKTUR HTML (berlaku untuk semua halaman ujian):

```html
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Langit Korea — [Nama Halaman]</title>

  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">

  <!-- Supabase -->
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

  <style>
    :root {
      --langit-biru    : #4A90D9;
      --langit-fajar   : #FF8C61;
      --putih-bersih   : #F8F9FF;
      --teks-utama     : #1E2A3A;
      --teks-sekunder  : #6B7A8D;
      --hijau-berhasil : #4CAF82;
      --merah-salah    : #E05C5C;
      --kuning-sedang  : #F5A623;
      --bg-soal-belum  : #E8EDF2;
      --bg-soal-jawab  : var(--langit-biru);
      --bg-soal-aktif  : var(--langit-fajar);
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--putih-bersih);
      color: var(--teks-utama);
      min-height: 100vh;
    }

    .korean-text {
      font-family: 'Noto Sans KR', sans-serif;
    }

    /* Tombol minimal 48px height untuk mobile */
    button { min-height: 48px; cursor: pointer; }

    /* Loading spinner */
    #loading {
      position: fixed; inset: 0;
      background: rgba(248,249,255,0.9);
      display: flex; align-items: center; justify-content: center;
      z-index: 999; display: none;
    }

    /* Pesan notifikasi */
    #pesan {
      position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
      padding: 12px 24px; border-radius: 24px;
      font-size: 14px; font-weight: 500;
      display: none; z-index: 1000; max-width: 90%;
      text-align: center;
    }
    .pesan-sukses { background: var(--hijau-berhasil); color: white; }
    .pesan-error  { background: var(--merah-salah);    color: white; }
    .pesan-info   { background: var(--langit-biru);    color: white; }
  </style>
</head>
<body>

  <!-- Loading overlay -->
  <div id="loading">
    <div style="text-align:center">
      <div style="font-size:32px;margin-bottom:8px">🌌</div>
      <p style="color:var(--teks-sekunder)">Memuat soal...</p>
    </div>
  </div>

  <!-- Pesan notifikasi -->
  <div id="pesan"></div>

  <!-- Konten halaman di sini -->

  <script>
    // GANTI DENGAN MILIKMU
    const SUPABASE_URL  = 'https://XXXXX.supabase.co'
    const SUPABASE_ANON = 'eyXXXXXXXXXXXXXXXXXXXXXXXX'
    const { createClient } = supabase
    const db = createClient(SUPABASE_URL, SUPABASE_ANON)

    // Helper functions
    function tampilkanLoading(aktif) {
      document.getElementById('loading').style.display = aktif ? 'flex' : 'none'
    }
    function tampilkanPesan(teks, tipe = 'info') {
      const el = document.getElementById('pesan')
      el.textContent = teks
      el.className = 'pesan-' + tipe
      el.style.display = 'block'
      setTimeout(() => el.style.display = 'none', 4000)
    }

    // Logika halaman di sini
  </script>
</body>
</html>
```

---

### KOMPONEN: GRID NAVIGASI SOAL

```javascript
// State management soal
const state = {
    soal: [],           // array soal dari Supabase
    jawaban: {},        // { nomor_tampil: 'a'/'b'/'c'/'d' }
    soalAktif: 1,       // nomor soal yang sedang ditampilkan
    timerDetik: 3000,   // 50 menit untuk simulasi, 25 menit untuk practice
    timerInterval: null,
    audioSedangBerjalan: false,
    audioPlayCount: 0,
    modeSoal: 'simulasi', // 'simulasi' atau 'practice'
}

// Render grid navigasi soal (40 atau 20 kotak)
function renderGrid() {
    const grid = document.getElementById('grid-soal')
    grid.innerHTML = ''

    state.soal.forEach(soal => {
        const n = soal.nomor_tampil
        const btn = document.createElement('button')
        btn.textContent = n
        btn.onclick = () => {
            if (state.audioSedangBerjalan) return // terkunci saat audio
            pindahSoal(n)
        }

        // Warna berdasarkan status
        if (n === state.soalAktif) {
            btn.style.background = 'var(--langit-fajar)'
            btn.style.color = 'white'
        } else if (state.jawaban[n]) {
            btn.style.background = 'var(--langit-biru)'
            btn.style.color = 'white'
        } else {
            btn.style.background = 'var(--bg-soal-belum)'
            btn.style.color = 'var(--teks-utama)'
        }

        // Terkunci saat audio berjalan
        if (state.audioSedangBerjalan) {
            btn.style.opacity = '0.4'
            btn.style.cursor = 'not-allowed'
        }

        btn.style.cssText += `
            width: 40px; height: 40px; border-radius: 8px;
            border: none; font-size: 13px; font-weight: 600;
            transition: all 0.15s ease;
        `
        grid.appendChild(btn)
    })
}

// Render soal aktif ke layar
function renderSoal() {
    const soal = state.soal.find(s => s.nomor_tampil === state.soalAktif)
    if (!soal) return

    const isListening = soal.tipe === 'mendengarkan'
    const container = document.getElementById('konten-soal')

    let html = `
        <div class="nomor-seksi" style="
            font-size: 12px; font-weight: 600; color: var(--teks-sekunder);
            text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
            ${isListening ? '🎧 Mendengarkan' : '📖 Membaca'} · Soal ${state.soalAktif}
        </div>
    `

    // Gambar soal (jika ada)
    if (soal.gambar_url) {
        html += `<img src="${soal.gambar_url}" alt="Gambar soal"
            style="width:100%;max-width:320px;border-radius:12px;margin-bottom:16px;">`
    }

    // Teks soal (Korea only — tidak ada terjemahan saat ujian)
    html += `
        <div class="teks-soal korean-text" style="
            font-size: 16px; line-height: 1.7; margin-bottom: 20px;
            padding: 16px; background: white; border-radius: 12px;
            border: 1px solid #E0E7EF;">
            ${soal.teks_soal}
        </div>
    `

    // Audio player (hanya untuk soal listening)
    if (isListening) {
        html += renderAudioPlayer(soal)
    }

    // Pilihan A-D
    html += `<div class="pilihan-container" style="display:flex;flex-direction:column;gap:10px;">`

    const pilihan = [
        { huruf: 'a', simbol: '①', teks: soal.pilihan_a, gambar: soal.pilihan_a_gambar_url },
        { huruf: 'b', simbol: '②', teks: soal.pilihan_b, gambar: soal.pilihan_b_gambar_url },
        { huruf: 'c', simbol: '③', teks: soal.pilihan_c, gambar: soal.pilihan_c_gambar_url },
        { huruf: 'd', simbol: '④', teks: soal.pilihan_d, gambar: soal.pilihan_d_gambar_url },
    ]

    pilihan.forEach(p => {
        const dipilih = state.jawaban[state.soalAktif] === p.huruf
        const warnaBg = dipilih ? 'var(--langit-biru)' : 'white'
        const warnaTeks = dipilih ? 'white' : 'var(--teks-utama)'
        const border = dipilih ? 'none' : '1px solid #E0E7EF'

        html += `
            <button onclick="pilihJawaban('${p.huruf}')"
                style="
                    display:flex; align-items:center; gap:12px; padding:14px 16px;
                    background:${warnaBg}; color:${warnaTeks}; border:${border};
                    border-radius:12px; text-align:left; width:100%;
                    font-family:'Noto Sans KR',sans-serif; font-size:15px;
                    transition: all 0.15s ease; min-height:52px;
                ">
                <span style="font-weight:700;font-size:16px;min-width:24px">${p.simbol}</span>
                ${p.gambar
                    ? `<img src="${p.gambar}" alt="Pilihan ${p.simbol}"
                        style="height:64px;border-radius:8px;object-fit:contain;">`
                    : `<span class="korean-text">${p.teks}</span>`
                }
            </button>
        `
    })

    html += `</div>`
    container.innerHTML = html
}

// Audio player untuk soal listening
function renderAudioPlayer(soal) {
    const sudahPlay = state.audioPlayCount > 0
    const terkunci = state.audioSedangBerjalan

    return `
        <div id="audio-player-wrapper" style="
            background: linear-gradient(135deg, #EEF5FD, #E8F0FA);
            border-radius: 16px; padding: 16px; margin-bottom: 16px;
            border: 1px solid #D0E4F5;">

            <audio id="audio-soal" src="${soal.audio_url || ''}" preload="auto"></audio>

            <div style="display:flex; align-items:center; gap:12px">
                <button id="btn-play-audio"
                    onclick="mainkanAudio()"
                    ${terkunci || sudahPlay ? 'disabled' : ''}
                    style="
                        width:52px; height:52px; border-radius:50%; border:none;
                        background:${sudahPlay ? 'var(--teks-sekunder)' : 'var(--langit-biru)'};
                        color:white; font-size:20px; flex-shrink:0;
                        opacity:${terkunci ? '0.5' : '1'};
                        cursor:${sudahPlay ? 'not-allowed' : 'pointer'};
                    ">
                    ${state.audioSedangBerjalan ? '⏸' : '▶️'}
                </button>

                <div>
                    <div style="font-size:13px;font-weight:600;color:var(--teks-utama)">
                        ${state.audioSedangBerjalan
                            ? '🔊 Audio sedang berjalan...'
                            : sudahPlay
                                ? '✅ Audio sudah diputar (tidak bisa diulang)'
                                : '🎧 Tekan ▶ untuk memulai audio'
                        }
                    </div>
                    <div style="font-size:11px;color:var(--teks-sekunder);margin-top:2px">
                        Audio akan berputar otomatis 2x
                    </div>
                </div>
            </div>

            ${state.audioSedangBerjalan ? `
                <div style="
                    height:4px; background:#D0E4F5; border-radius:2px;
                    margin-top:12px; overflow:hidden;">
                    <div id="audio-progress" style="
                        height:100%; background:var(--langit-biru);
                        border-radius:2px; width:0%;
                        transition:width 0.1s linear;">
                    </div>
                </div>
            ` : ''}
        </div>
    `
}

// Mainkan audio listening (2x otomatis, tidak bisa diulang)
let audioPlayRound = 0

function mainkanAudio() {
    const soalAktif = state.soal.find(s => s.nomor_tampil === state.soalAktif)
    if (!soalAktif || !soalAktif.audio_url) {
        // Jika tidak ada audio URL (fallback: baca teks audio)
        bacaAudioTTS(soalAktif.audio_teks)
        return
    }

    const audio = document.getElementById('audio-soal')
    if (!audio) return

    audioPlayRound = 0
    state.audioSedangBerjalan = true
    state.audioPlayCount++
    kunciNavigasi(true)
    renderSoal()
    renderGrid()

    audio.play()
    audio.onended = () => {
        audioPlayRound++
        if (audioPlayRound < 2) {
            // Putar kedua kali
            audio.currentTime = 0
            audio.play()
        } else {
            // Selesai 2x
            state.audioSedangBerjalan = false
            kunciNavigasi(false)
            renderSoal()
            renderGrid()
        }
    }

    // Update progress bar
    audio.ontimeupdate = () => {
        const progress = document.getElementById('audio-progress')
        if (progress && audio.duration) {
            const pct = (audio.currentTime / audio.duration) * 100
            progress.style.width = pct + '%'
        }
    }
}

// Fallback TTS jika tidak ada audio file
function bacaAudioTTS(teks) {
    if (!teks || !window.speechSynthesis) return
    const utterance = new SpeechSynthesisUtterance(teks)
    utterance.lang = 'ko-KR'
    utterance.rate = 0.9

    audioPlayRound = 0
    state.audioSedangBerjalan = true
    kunciNavigasi(true)
    renderSoal()

    utterance.onend = () => {
        audioPlayRound++
        if (audioPlayRound < 2) {
            window.speechSynthesis.speak(utterance)
        } else {
            state.audioSedangBerjalan = false
            kunciNavigasi(false)
            renderSoal()
            renderGrid()
        }
    }

    window.speechSynthesis.speak(utterance)
}

// Kunci/buka navigasi saat audio berjalan
function kunciNavigasi(kunci) {
    const btnPrev = document.getElementById('btn-prev')
    const btnNext = document.getElementById('btn-next')
    if (btnPrev) { btnPrev.disabled = kunci; btnPrev.style.opacity = kunci ? '0.4' : '1' }
    if (btnNext) { btnNext.disabled = kunci; btnNext.style.opacity = kunci ? '0.4' : '1' }
}
```

---

### KOMPONEN: TIMER

```javascript
function mulaiTimer(totalDetik) {
    state.timerDetik = totalDetik

    state.timerInterval = setInterval(() => {
        state.timerDetik--
        renderTimer()

        if (state.timerDetik <= 0) {
            clearInterval(state.timerInterval)
            selesaikanUjian('waktu_habis')
        }
    }, 1000)
}

function renderTimer() {
    const el = document.getElementById('timer')
    if (!el) return

    const menit = Math.floor(state.timerDetik / 60)
    const detik = state.timerDetik % 60
    const teks = `${String(menit).padStart(2,'0')}:${String(detik).padStart(2,'0')}`

    el.textContent = teks

    // Merah saat < 5 menit
    el.style.color = state.timerDetik < 300 ? 'var(--merah-salah)' : 'var(--teks-utama)'
    el.style.fontWeight = state.timerDetik < 300 ? '700' : '600'

    // Animasi pulse saat < 1 menit
    if (state.timerDetik < 60) {
        el.style.animation = 'pulse 1s infinite'
    }
}
```

---

### KOMPONEN: SELESAIKAN UJIAN & HITUNG SKOR

```javascript
async function selesaikanUjian(alasan = 'selesai') {
    clearInterval(state.timerInterval)

    // Hitung skor
    let skorReading = 0
    let skorListening = 0
    const detailJawaban = []

    state.soal.forEach(soal => {
        const jawabanUser = state.jawaban[soal.nomor_tampil]
        const benar = jawabanUser === soal.jawaban

        if (soal.tipe === 'membaca' && benar) skorReading += 5
        if (soal.tipe === 'mendengarkan' && benar) skorListening += 5

        detailJawaban.push({
            soal_id:      soal.id,
            nomor:        soal.nomor_tampil,
            tipe:         soal.tipe,
            tipe_soal_ujian: soal.tipe_soal_ujian,
            jawaban_user: jawabanUser || null,
            jawaban_benar:soal.jawaban,
            benar:        benar
        })
    })

    const skorTotal = skorReading + skorListening
    const lulus = skorTotal >= (state.modeSoal === 'simulasi' ? 80 : 40)
    const durasiDetik = (state.modeSoal === 'simulasi' ? 3000 : 1500) - state.timerDetik

    // Simpan ke Supabase
    await simpanHasilUjian(skorReading, skorListening, skorTotal, durasiDetik, detailJawaban)

    // Redirect ke halaman hasil
    const params = new URLSearchParams({
        skor_reading:   skorReading,
        skor_listening: skorListening,
        skor_total:     skorTotal,
        lulus:          lulus,
        mode:           state.modeSoal,
        alasan:         alasan
    })

    // Simpan detail ke sessionStorage untuk halaman hasil
    sessionStorage.setItem('detail_jawaban', JSON.stringify(detailJawaban))
    sessionStorage.setItem('soal_ujian', JSON.stringify(state.soal))

    window.location.href = `hasil-simulasi.html?${params.toString()}`
}
```

---

### HALAMAN HASIL: `hasil-simulasi.html`

#### Konten yang ditampilkan:

```
1. SKOR UTAMA
   ┌─────────────────────┐
   │     Skor Kamu       │
   │      142/200        │
   │  ★★★★☆  Hampir!   │
   └─────────────────────┘

2. BREAKDOWN
   Reading   : 72/100
   Listening : 70/100

3. STATUS LULUS/TIDAK
   ✅ LULUS  → "Selamat! Kamu melampaui skor minimum 80."
   ❌ BELUM  → "Kamu perlu 80 poin. Masih kurang X poin lagi."

4. ANALISA KELEMAHAN (Langit Korea exclusive)
   Tipe soal yang paling banyak salah → rekomendasi latihan

5. REVIEW JAWABAN
   - Free: lihat soal + jawaban kamu vs yang benar (tanpa penjelasan)
   - Premium: + penjelasan Bahasa Indonesia per soal

6. PESAN MOTIVASI (Mode Teman)
   Skor 90–100%: "Luar biasa! Kamu hampir siap ujian sungguhan 🚀"
   Skor 70–89%:  "Bagus! Sedikit lagi sampai ke skor aman."
   Skor 50–69%:  "Progresmu bagus! Yuk fokus di bagian yang lemah."
   Skor <50%:    "Tidak apa-apa, ini masih latihan. Kamu bisa!"

7. CTA
   [Coba Lagi]  [Latihan Soal]  [Lihat Materi]
```

---

## ✅ CHECKLIST SEBELUM BUILD

```
[ ] Supabase URL + anon key sudah siap
[ ] Tabel soal_eps sudah ada kolom tipe_soal_ujian
[ ] Minimal 1 set soal sudah di-insert ke database
[ ] Bucket storage sudah ada untuk audio (audio-listening)
[ ] Halaman global.css sudah ada dengan CSS variables
[ ] File icon-back.png, icon-settings.png sudah di assets/icons/
```

---

## 🚀 CARA BUILD DI ZED (BERURUTAN)

```
Step 1: Kirim request ke Zed:
  "Buat briefing.html berdasarkan prompt ini"

Step 2: Preview di browser, cek tampilan

Step 3:
  "Buat practice.html berdasarkan prompt ini"

Step 4:
  "Buat simulasi.html berdasarkan prompt ini"

Step 5:
  "Buat hasil-simulasi.html berdasarkan prompt ini"

Step 6: Konek ke Supabase, test dengan soal unit 31
```
