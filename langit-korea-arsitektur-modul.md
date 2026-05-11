# 🌌 LANGIT KOREA — ARSITEKTUR KONTEN & PROMPT ZED
# Panduan lengkap merombak sistem menjadi Modul Belajar + Simulasi Ujian
# Berdasarkan analisa mendalam Textbook 2 (30 unit, 9 halaman/unit)

---

## 🔬 TEMUAN DARI BEDAH TEXTBOOK

Setiap unit punya 4 JENIS KONTEN berbeda yang selama ini diperlakukan sama:

```
HAL 1 — VOCAB 1          → Kosakata + gambar + LATIHAN COCOKKAN (연결하세요)
HAL 2 — GRAMMAR 1        → Pola kalimat + LATIHAN PILIH & LENGKAPI
HAL 3 — PERCAKAPAN 1     → Dialog situasi kerja + PERTANYAAN PEMAHAMAN
HAL 4 — VOCAB 2          → Kosakata + gambar + LATIHAN LENGKAPI KALIMAT
HAL 5 — GRAMMAR 2        → Pola kalimat + LATIHAN TRANSFORMASI
HAL 6 — PERCAKAPAN 2     → Dialog + PERTANYAAN + role-play expressions
HAL 7 — BUDAYA & INFO    → Artikel budaya Korea + SELF ASSESSMENT checklist
HAL 8 — SOAL MEMBACA     → 5 soal pilihan ganda EPS-TOPIK ← sudah ada
HAL 9 — SOAL LISTENING   → 5 soal + skrip audio EPS-TOPIK ← sudah ada
```

### Tipe Latihan yang Ada di Halaman Materi:
```
연결하세요          → Cocokkan (gambar ↔ kata/kalimat)
문장을 완성하세요   → Lengkapi kalimat (pilih dari kotak kata)
대화를 완성하세요   → Lengkapi dialog (pilih kata yang sesuai)
알맞은 것을 골라    → Pilih yang benar dari opsi
보기와 같이 쓰세요  → Tulis kalimat mengikuti contoh (produksi)
대답해 봐요!        → Jawab pertanyaan pemahaman percakapan
```

---

## 🏗️ ARSITEKTUR MODUL BARU

### Struktur per Unit (contoh: Unit 31)

```
UNIT 31 — 복장과 근무 태도 (Pakaian & Sikap Kerja)
│
├── 📌 INTRO UNIT
│   └── Judul + topik + apa yang akan dipelajari
│
├── 🔤 SEKSI 1: KOSAKATA (dari hal 1 + hal 4)
│   ├── MODE BELAJAR (Interaktif)
│   │   ├── Flashcard: gambar + kata Korea + terjemahan
│   │   ├── Latihan Cocokkan (drag/tap gambar ke kata)
│   │   └── Latihan Lengkapi Kalimat (pilih dari kotak)
│   └── MODE SERIUS (Pilihan Ganda)
│       └── 4 soal pilihan ganda dari kosakata unit ini
│
├── 📖 SEKSI 2: GRAMMAR (dari hal 2 + hal 5)
│   ├── MODE BELAJAR (Interaktif)
│   │   ├── Kartu pola: rumus + contoh kalimat + audio
│   │   ├── Latihan Pilih kata yang tepat
│   │   └── Latihan Lengkapi dialog
│   └── MODE SERIUS (Pilihan Ganda)
│       └── 4 soal pilihan ganda pola grammar
│
├── 💬 SEKSI 3: PERCAKAPAN (dari hal 3 + hal 6)
│   ├── MODE BELAJAR (Interaktif)
│   │   ├── Dialog + audio (tiap baris tap untuk dengar)
│   │   ├── Pertanyaan pemahaman: 대답해 봐요!
│   │   └── Situasi kerja nyata: contoh ekspresi
│   └── MODE SERIUS
│       └── Soal pemahaman dialog (pilihan ganda)
│
├── 🌏 SEKSI 4: BUDAYA (dari hal 7)
│   ├── Artikel singkat (bahasa Korea + terjemahan Indonesia)
│   ├── Self Assessment Checklist
│   └── Pertanyaan pemahaman sederhana
│
└── ✅ MINI TEST UNIT (dari hal 8 + hal 9)
    ├── 5 soal MEMBACA (format ujian asli)
    └── 5 soal LISTENING (format ujian asli + audio)
```

---

## 📦 SCHEMA DATABASE LENGKAP (UPDATE)

### Tabel baru: `latihan_interaktif`
```sql
CREATE TABLE public.latihan_interaktif (
  id            serial PRIMARY KEY,
  unit          integer NOT NULL,           -- 31-60
  seksi         text NOT NULL CHECK (seksi IN (
                  'vocab1','vocab2','grammar1','grammar2',
                  'conversation1','conversation2','budaya')),
  tipe_latihan  text NOT NULL CHECK (tipe_latihan IN (
                  'flashcard',              -- tampilkan kata + gambar
                  'cocokkan',               -- drag/tap cocokkan
                  'pilih_kata',             -- pilih dari kotak kata
                  'lengkapi_dialog',        -- isi kosong dalam dialog
                  'pilihan_ganda',          -- format ujian
                  'pemahaman_dialog')),     -- jawab pertanyaan dialog
  urutan        integer DEFAULT 1,
  -- Konten utama
  teks_korea    text,                       -- teks Korea
  teks_indo     text,                       -- terjemahan Indonesia
  teks_inggris  text,                       -- terjemahan Inggris (dari buku)
  gambar_url    text,
  audio_url     text,
  -- Untuk latihan cocokkan
  pasangan      jsonb,  -- [{"soal":"지퍼를 올렸어요.","jawaban":"to zip up"}]
  -- Untuk pilih kata / lengkapi
  kalimat       text,   -- kalimat dengan ___ kosong
  opsi          jsonb,  -- ["짧다","싸다","재미있다","단정하다"]
  jawaban       text,
  -- Untuk dialog
  dialog        jsonb,  -- [{"speaker":"가","teks":"기분이 ___."},...]
  konteks       text,   -- petunjuk konteks situasi
  -- Metadata
  akses         text DEFAULT 'free',
  created_at    timestamptz DEFAULT now()
);

ALTER TABLE public.latihan_interaktif ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Latihan free publik"
  ON public.latihan_interaktif FOR SELECT
  TO anon, authenticated USING (akses = 'free');
```

### Update tabel `soal_eps` (tambah kolom)
```sql
ALTER TABLE public.soal_eps
  ADD COLUMN IF NOT EXISTS sumber text DEFAULT 'textbook'
    CHECK (sumber IN ('textbook', 'open_test')),
  ADD COLUMN IF NOT EXISTS tahun_soal integer,    -- untuk open test
  ADD COLUMN IF NOT EXISTS nomor_asli integer;    -- nomor soal di sumber asli
```

---

## 🎮 DETAIL FORMAT LATIHAN INTERAKTIF

### 1. FLASHCARD (untuk kosakata baru)
```json
{
  "tipe_latihan": "flashcard",
  "teks_korea": "작업복",
  "teks_indo": "baju kerja",
  "teks_inggris": "work clothes",
  "gambar_url": "...",
  "audio_url": "..."
}
```
**UI:** Kartu bisa diflip. Depan: gambar. Belakang: kata Korea + terjemahan.
**Interaksi:** Swipe kiri (belum hafal) / kanan (sudah hafal).

### 2. COCOKKAN (연결하세요 dari hal 1 + hal 4)
```json
{
  "tipe_latihan": "cocokkan",
  "konteks": "Cocokkan gambar dengan kata yang sesuai",
  "pasangan": [
    {"soal": "[gambar_zipup]",  "jawaban": "지퍼를 올렸어요."},
    {"soal": "[gambar_button]", "jawaban": "단추를 잠갔어요."},
    {"soal": "[gambar_unbutton]","jawaban": "단추를 풀었어요."},
    {"soal": "[gambar_tie]",    "jawaban": "넥타이를 맸어요."}
  ]
}
```
**UI:** Kolom kiri = gambar, kolom kanan = teks (diacak). User tap gambar → tap teks → garis menghubungkan.

### 3. PILIH KATA (알맞은 것을 골라 dari hal 2 + hal 5)
```json
{
  "tipe_latihan": "pilih_kata",
  "opsi": ["짧다", "싸다", "재미있다", "단정하다"],
  "soal": [
    {"kalimat": "칼로 씨는 ___ 이야기를 해요.", "jawaban": "재미있게"},
    {"kalimat": "마두 씨는 항상 옷을 ___ 입어요.", "jawaban": "단정하게"},
    {"kalimat": "시장에 가면 옷을 ___ 살 수 있어요.", "jawaban": "싸게"},
    {"kalimat": "날씨가 더워서 머리를 ___ 잘랐어요.", "jawaban": "짧게"}
  ]
}
```
**UI:** Kotak kata di atas (bisa di-tap). Kalimat dengan slot kosong di bawah. Tap kata → masuk ke slot.

### 4. LENGKAPI DIALOG (대화를 완성하세요 dari hal 2 + hal 5)
```json
{
  "tipe_latihan": "lengkapi_dialog",
  "opsi": ["넓다", "작다", "아프다", "불편하다"],
  "dialog": [
    {
      "nomor": 1,
      "garis": [
        {"speaker": "가", "teks": "칼로 씨, 의자가 ___."},
        {"speaker": "나", "teks": "아니에요, 아주 편해요."}
      ],
      "jawaban": "불편해 보여요"
    },
    {
      "nomor": 2,
      "garis": [
        {"speaker": "가", "teks": "자야 씨, ___."},
        {"speaker": "나", "teks": "맞아요. 감기에 걸려서 머리가 좀 아파요."}
      ],
      "jawaban": "아파 보여요"
    }
  ]
}
```
**UI:** Dialog ditampilkan satu per satu. Slot kosong berwarna berbeda. Tap → muncul pilihan.

### 5. PEMAHAMAN DIALOG (대답해 봐요! dari hal 3 + hal 6)
```json
{
  "tipe_latihan": "pemahaman_dialog",
  "dialog_ref": "percakapan_31_1",
  "pertanyaan": [
    {
      "teks": "새 작업복이 어때요?",
      "teks_indo": "Bagaimana baju kerja barunya?",
      "tipe": "pilihan_ganda",
      "pilihan": [
        "무겁지만 안전해요.",
        "가벼워서 좋아요.",
        "지퍼가 없어서 불편해요.",
        "예전 작업복보다 커요."
      ],
      "jawaban": 1
    },
    {
      "teks": "왜 작업복의 지퍼를 올려야 해요?",
      "teks_indo": "Kenapa resleting baju kerja harus dinaikkan?",
      "tipe": "pilihan_ganda",
      "pilihan": [
        "더워서요.",
        "예뻐 보여서요.",
        "안전하고 단정해 보여서요.",
        "반장님이 싫어해서요."
      ],
      "jawaban": 2
    }
  ]
}
```

---

## 🎯 MODE SERIUS — Pilihan Ganda dari Materi

Setiap seksi punya versi "mode serius" — soal pilihan ganda yang dibuat dari konten materi.
Ini BERBEDA dari soal EPS-TOPIK (hal 8-9) — ini latihan dari dalam materi itu sendiri.

```json
{
  "tipe_latihan": "pilihan_ganda",
  "seksi": "vocab1",
  "soal": "다음 단어의 뜻을 고르십시오. '단정하다'",
  "soal_indo": "Pilih arti kata berikut: '단정하다'",
  "pilihan_a": "rapi / berpenampilan bersih",
  "pilihan_b": "tidak sopan",
  "pilihan_c": "sulit dimengerti",
  "pilihan_d": "berbahaya",
  "jawaban": "a",
  "penjelasan_id": "'단정하다' artinya berpenampilan rapi dan bersih. Sering dipakai untuk menggambarkan penampilan yang sesuai aturan di tempat kerja."
}
```

---

## 🚀 ALUR BELAJAR USER DI MODUL

```
User buka Unit 31
       ↓
[INTRO] Apa yang akan dipelajari + perkiraan waktu (~25 menit)
       ↓
[KOSAKATA] Mode Belajar dulu
  → Flashcard 8 kata kunci
  → Latihan Cocokkan (gambar ↔ kata kerja)
  → Mode Serius: 4 soal pilihan ganda kosakata
       ↓
[GRAMMAR] Pola -아/어 보이다
  → Penjelasan + 3 contoh kalimat
  → Latihan Pilih Kata (4 kalimat)
  → Latihan Lengkapi Dialog (4 dialog)
  → Mode Serius: 4 soal pilihan ganda grammar
       ↓
[PERCAKAPAN] Dialog di tempat kerja
  → Baca/dengar dialog (tiap baris tap)
  → Jawab: 대답해 봐요! (2 pertanyaan pemahaman)
  → Contoh ekspresi untuk situasi serupa
       ↓
[BUDAYA] Tata bahasa panggilan di tempat kerja Korea
  → Baca artikel singkat
  → Self Assessment: 3 checklist
       ↓
[MINI TEST] Format ujian EPS-TOPIK asli
  → 5 soal Membaca (hal 8)
  → 5 soal Listening (hal 9)
  → Hasil: skor + review per soal
       ↓
[SELESAI] Progress tersimpan, unit berikutnya terbuka
```

---

## 📋 YANG PERLU DIKERJAKAN DI ZED (BERURUTAN)

### FASE 1: Database
```
1. Jalankan SQL setup tabel latihan_interaktif di Supabase
2. Update kolom soal_eps (tambah sumber, tahun_soal, nomor_asli)
```

### FASE 2: Script Ekstraksi Latihan (Python)
```
Buat: extract_latihan.py
→ Baca setiap unit PDF
→ Ekstrak konten latihan per seksi (vocab/grammar/conv/budaya)
→ Susun ke format JSON latihan_interaktif
→ Upload ke Supabase
```

### FASE 3: Halaman Modul Belajar (HTML/JS)
```
Buat: modul-unit.html
→ Navigasi seksi (Kosakata | Grammar | Percakapan | Budaya | Mini Test)
→ Flashcard component
→ Latihan Cocokkan component
→ Latihan Pilih Kata component
→ Latihan Dialog component
→ Mini Test component (reuse dari latihan-eps.html)
```

### FASE 4: Download & Proses Open Test
```
Download dari eps.go.kr → Open Test PDF
Buat: extract_open_test.py
→ Ekstrak 40 soal per set
→ Tandai sumber='open_test' + tahun
→ Upload ke soal_eps
```

### FASE 5: Halaman Simulasi (pakai soal open_test)
```
Update: simulasi.html
→ Query soal WHERE sumber = 'open_test'
→ Distribusi sesuai format ujian asli
```

---

## 📌 KUNCI KEBERHASILAN

1. **Latihan interaktif TIDAK menerjemahkan soal** — teks Korea tetap Korea
   (teks_indo hanya tersedia sebagai hint opsional untuk pemula)

2. **Mode Belajar → Mode Serius** dalam satu unit — user tidak bisa skip

3. **Audio ada di semua seksi** — vocab (per kata), grammar (per contoh),
   percakapan (per dialog), mini test (listening)

4. **Progress per seksi tersimpan** — user bisa lanjut dari mana saja

5. **Open Test terpisah dari Textbook** — simulasi ujian pakai soal yang
   belum pernah dilihat user (bukan soal yang sudah dipelajari di modul)
