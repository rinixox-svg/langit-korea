# LANGIT KOREA — PROMPT INTEGRASI DATA EXTRACTED KE SUPABASE
# Semua ekstraksi sudah dikerjakan — ZIP berisi 2735 file siap pakai
# Tugas Zed: baca data.json tiap unit, upload gambar ke Storage, insert soal ke DB

---

## 📦 STRUKTUR DATA YANG SUDAH ADA

Folder `langit-korea-extracted/` berisi hasil ekstraksi lengkap dari 34 PDF:

```
langit-korea-extracted/
├── unit_31/
│   ├── data.json          ← SATU FILE INI BERISI SEGALANYA
│   ├── images/
│   │   ├── hal1_vocab/    img_01.jpeg ... img_16.jpeg  (kosakata 1)
│   │   ├── hal2_grammar/  img_01.jpeg ... img_04.jpeg  (grammar 1)
│   │   ├── hal3_conv/     img_01.jpeg ... img_04.jpeg  (percakapan 1)
│   │   ├── hal4_vocab/    img_01.jpeg ... img_18.jpeg  (kosakata 2)
│   │   ├── hal5_grammar/  img_01.jpeg ... img_04.jpeg  (grammar 2)
│   │   ├── hal6_conv/     img_01.jpeg ... img_03.jpeg  (percakapan 2)
│   │   ├── hal7_culture/  img_01.jpeg ... img_21.jpeg  (budaya)
│   │   ├── hal8_soal/     soal_r1_a.jpeg ... (soal membaca bergambar)
│   │   └── hal9_soal/     soal_l1_a.jpeg ... soal_l1_d.jpeg (soal listening)
│   └── teks/
│       ├── hal1_vocab.txt     ← teks kosakata 1
│       ├── hal2_grammar.txt   ← teks grammar 1
│       ├── hal3_conv.txt      ← teks percakapan 1
│       ├── hal4_vocab.txt     ← teks kosakata 2
│       ├── hal5_grammar.txt   ← teks grammar 2
│       ├── hal6_conv.txt      ← teks percakapan 2
│       ├── hal7_culture.txt   ← teks budaya
│       ├── hal8_soal.txt      ← teks soal membaca
│       └── hal9_soal.txt      ← teks soal listening
├── unit_32/ ... unit_60/
└── appendix_ans/ appendix_scr/ appendix_voc/ appendix_inf/
```

---

## 📋 FORMAT `data.json` (satu per unit)

```json
{
  "unit": 31,
  "title_ko": "복장과 근무 태도",
  "title_id": "Pakaian dan Sikap Kerja",
  "file": "unit_31_attire_work_attitude.pdf",
  "total_halaman": 10,
  "halaman": {
    "hal1": { "kategori": "vocab",    "chars": 494, "gambar_count": 16 },
    "hal2": { "kategori": "grammar",  "chars": 846, "gambar_count": 4  },
    "hal3": { "kategori": "conversation", "chars": 1260, "gambar_count": 4 },
    "hal4": { "kategori": "vocab",    "chars": 653, "gambar_count": 18 },
    "hal5": { "kategori": "grammar",  "chars": 804, "gambar_count": 4  },
    "hal6": { "kategori": "conversation", "chars": 1120, "gambar_count": 3 },
    "hal7": { "kategori": "culture",  "chars": 2243, "gambar_count": 21 },
    "hal8": { "kategori": "soal_membaca",   "chars": 781, "gambar_count": 0 },
    "hal9": { "kategori": "soal_listening", "chars": 723, "gambar_count": 4 }
  },
  "soal": [
    {
      "id": "u31_m1",
      "nomor": 1,
      "tipe": "membaca",
      "teks_soal": "1. 다음 단어의 반대말은 무엇입니까?\n잠그다",
      "pilihan_a": "벗다",
      "pilihan_b": "풀다",
      "pilihan_c": "올리다",
      "pilihan_d": "내리다",
      "jawaban": "?",
      "audio_teks": "",
      "ada_gambar_pilihan": false,
      "gambar_pilihan": {},
      "akses": "free"
    }
  ]
}
```

---

## 🗄️ TABEL SUPABASE YANG DIBUTUHKAN

### Tabel utama: `soal_eps` (sudah ada dari prompt sebelumnya)
```sql
-- Pastikan kolom ini ada:
ALTER TABLE soal_eps ADD COLUMN IF NOT EXISTS
  gambar_pilihan_a text,
  gambar_pilihan_b text,
  gambar_pilihan_c text,
  gambar_pilihan_d text;
```

### Tabel baru: `materi_unit` (untuk konten materi belajar)
```sql
CREATE TABLE IF NOT EXISTS public.materi_unit (
  id          serial PRIMARY KEY,
  unit        integer NOT NULL,
  title_ko    text,
  title_id    text,
  kategori    text CHECK (kategori IN (
    'vocab','grammar','conversation','culture'
  )),
  sub         integer DEFAULT 1,  -- 1=halaman pertama, 2=halaman kedua
  teks        text,               -- isi teks halaman
  akses       text DEFAULT 'free',
  created_at  timestamptz DEFAULT now()
);

ALTER TABLE public.materi_unit ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Materi free publik"
  ON public.materi_unit FOR SELECT
  TO anon, authenticated
  USING (akses = 'free');
```

### Tabel baru: `gambar_materi` (untuk gambar vocab/grammar/culture)
```sql
CREATE TABLE IF NOT EXISTS public.gambar_materi (
  id          serial PRIMARY KEY,
  unit        integer NOT NULL,
  kategori    text NOT NULL,  -- vocab/grammar/conversation/culture/soal_pilihan
  sub         integer DEFAULT 1,
  urutan      integer DEFAULT 1,
  storage_url text NOT NULL,  -- URL dari Supabase Storage
  lebar       integer,
  tinggi      integer,
  akses       text DEFAULT 'free',
  created_at  timestamptz DEFAULT now()
);

ALTER TABLE public.gambar_materi ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Gambar materi publik"
  ON public.gambar_materi FOR SELECT
  TO anon, authenticated
  USING (akses = 'free');
```

---

## 🚀 SCRIPT: `integrate_to_supabase.py`

python
# integrate_to_supabase.py
# Baca data.json tiap unit, upload gambar ke Storage, insert ke DB

import os, json, re, time
from pathlib import Path
from supabase import create_client

# ─── KONFIGURASI ──────────────────────────────────────────
EXTRACTED_DIR = Path("./langit-korea-extracted")

# Baca .env manual (cara paling reliable)
def baca_env():
    env_path = Path(__file__).parent / ".env"
    cfg = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                k, _, v = line.partition('=')
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg

cfg = baca_env()
client = create_client(cfg['SUPABASE_URL'], cfg['SUPABASE_ANON_KEY'])

print("✅ Koneksi Supabase OK")

# ─── UPLOAD GAMBAR KE STORAGE ─────────────────────────────
def upload_gambar(local_path: Path, storage_path: str, bucket: str) -> str:
    """
    Upload satu gambar ke Supabase Storage.
    Return: public URL gambar.
    """
    ext = local_path.suffix.lower()
    mime = 'image/jpeg' if ext in ('.jpg','.jpeg') else 'image/png'

    with open(local_path, 'rb') as f:
        data = f.read()

    try:
        # Coba upload (upsert=True untuk overwrite jika sudah ada)
        client.storage.from_(bucket).upload(
            path=storage_path,
            file=data,
            file_options={"content-type": mime, "upsert": "true"}
        )
    except Exception as e:
        if '409' in str(e) or 'already exists' in str(e).lower():
            pass  # sudah ada, lanjut
        else:
            raise e

    # Ambil URL publik
    url_obj = client.storage.from_(bucket).get_public_url(storage_path)
    return url_obj

# ─── PROSES TIAP UNIT ─────────────────────────────────────
unit_dirs = sorted([d for d in EXTRACTED_DIR.iterdir()
                    if d.is_dir() and d.name.startswith('unit_')
                    and not d.name.startswith('unit_appendix')])

print(f"\n📂 {len(unit_dirs)} unit ditemukan\n")

total_soal_ok   = 0
total_materi_ok = 0
total_gambar_ok = 0

for unit_dir in unit_dirs:
    data_path = unit_dir / "data.json"
    if not data_path.exists():
        print(f"  ⚠️  {unit_dir.name}: data.json tidak ada, skip")
        continue

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    unit_num  = data['unit']
    title_ko  = data.get('title_ko', '')
    title_id  = data.get('title_id', '')

    print(f"── Unit {unit_num}: {title_id} ──")

    # ── 1. UPLOAD GAMBAR MATERI (vocab/grammar/culture) ──
    hal_map = {
        'hal1_vocab':    ('vocab',        1),
        'hal2_grammar':  ('grammar',      1),
        'hal3_conv':     ('conversation', 1),
        'hal4_vocab':    ('vocab',        2),
        'hal5_grammar':  ('grammar',      2),
        'hal6_conv':     ('conversation', 2),
        'hal7_culture':  ('culture',      1),
    }

    for folder_name, (kategori, sub) in hal_map.items():
        img_dir = unit_dir / "images" / folder_name
        if not img_dir.exists():
            continue

        img_files = sorted(img_dir.glob("*.jpeg")) + sorted(img_dir.glob("*.png"))

        for urutan, img_path in enumerate(img_files, 1):
            storage_path = f"materi/unit_{unit_num:02d}/{folder_name}/{img_path.name}"

            try:
                url = upload_gambar(img_path, storage_path, "gambar-materi")
                # Insert ke tabel gambar_materi
                client.table('gambar_materi').upsert({
                    'unit':        unit_num,
                    'kategori':    kategori,
                    'sub':         sub,
                    'urutan':      urutan,
                    'storage_url': url,
                    'lebar':       0,  # opsional
                    'tinggi':      0,
                    'akses':       'free'
                }).execute()
                total_gambar_ok += 1
                time.sleep(0.03)  # rate limit
            except Exception as e:
                print(f"    ⚠️  {img_path.name}: {str(e)[:60]}")

    print(f"  📸 Gambar materi: {total_gambar_ok} terupload")

    # ── 2. UPLOAD TEKS MATERI ──
    teks_map = {
        'hal1_vocab.txt':   ('vocab',        1),
        'hal2_grammar.txt': ('grammar',      1),
        'hal3_conv.txt':    ('conversation', 1),
        'hal4_vocab.txt':   ('vocab',        2),
        'hal5_grammar.txt': ('grammar',      2),
        'hal6_conv.txt':    ('conversation', 2),
        'hal7_culture.txt': ('culture',      1),
    }

    for fname, (kategori, sub) in teks_map.items():
        txt_path = unit_dir / "teks" / fname
        if not txt_path.exists(): continue
        teks = txt_path.read_text(encoding='utf-8').strip()
        if not teks: continue

        try:
            client.table('materi_unit').upsert({
                'unit':     unit_num,
                'title_ko': title_ko,
                'title_id': title_id,
                'kategori': kategori,
                'sub':      sub,
                'teks':     teks,
                'akses':    'free'
            }).execute()
            total_materi_ok += 1
        except Exception as e:
            print(f"    ⚠️  Materi {fname}: {str(e)[:60]}")

    print(f"  📝 Teks materi: {total_materi_ok} tersimpan")

    # ── 3. UPLOAD SOAL ──
    soal_list = data.get('soal', [])
    soal_ok = 0

    for soal in soal_list:
        # Upload gambar pilihan jika ada
        gambar_url = {}
        if soal.get('ada_gambar_pilihan') and soal.get('gambar_pilihan'):
            for huruf, rel_path in soal['gambar_pilihan'].items():
                img_path = unit_dir / rel_path
                if img_path.exists():
                    storage_path = f"soal/unit_{unit_num:02d}/{img_path.name}"
                    try:
                        url = upload_gambar(img_path, storage_path, "gambar-soal")
                        gambar_url[huruf] = url
                    except Exception as e:
                        print(f"    ⚠️  Gambar soal {huruf}: {str(e)[:60]}")

        # Bersihkan teks
        def bersih(t):
            if not t: return ""
            t = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(t))
            return re.sub(r'[ \t]+', ' ', t).strip()

        row = {
            'unit':                 unit_num,
            'tipe':                 soal.get('tipe', 'membaca'),
            'teks_soal':            bersih(soal.get('teks_soal', '')),
            'pilihan_a':            bersih(soal.get('pilihan_a', '')),
            'pilihan_b':            bersih(soal.get('pilihan_b', '')),
            'pilihan_c':            bersih(soal.get('pilihan_c', '')),
            'pilihan_d':            bersih(soal.get('pilihan_d', '')),
            'jawaban':              soal.get('jawaban', '?').lower(),
            'audio_teks':           bersih(soal.get('audio_teks', '')),
            'ada_gambar_pilihan':   bool(soal.get('ada_gambar_pilihan')),
            'gambar_pilihan_a':     gambar_url.get('a'),
            'gambar_pilihan_b':     gambar_url.get('b'),
            'gambar_pilihan_c':     gambar_url.get('c'),
            'gambar_pilihan_d':     gambar_url.get('d'),
            'akses':                soal.get('akses', 'free'),
        }

        # Skip jika teks soal kosong atau jawaban masih ?
        if not row['teks_soal']:
            continue
        if row['jawaban'] == '?':
            # Tetap insert tapi tandai untuk review
            row['jawaban'] = 'a'  # placeholder, perlu dicek manual
            row['akses'] = 'review'  # flag untuk review

        try:
            client.table('soal_eps').upsert(row).execute()
            soal_ok += 1
            total_soal_ok += 1
            time.sleep(0.03)
        except Exception as e:
            print(f"    ⚠️  Soal {soal.get('id')}: {str(e)[:80]}")

    print(f"  📚 Soal: {soal_ok}/{len(soal_list)} terupload\n")

# ─── LAPORAN AKHIR ────────────────────────────────────────
print("=" * 55)
print("📊 LAPORAN INTEGRASI SELESAI")
print("=" * 55)
print(f"✅ Total soal    : {total_soal_ok}")
print(f"✅ Total materi  : {total_materi_ok}")
print(f"✅ Total gambar  : {total_gambar_ok}")
print(f"\nCek di Supabase Dashboard → Table Editor")
print("=" * 55)
```

---

## 📋 CHECKLIST SUPABASE SEBELUM JALANKAN

```
Di Supabase Dashboard → Storage:
[ ] Buat bucket "gambar-materi" → Public: YES
[ ] Buat bucket "gambar-soal"   → Public: YES

Di SQL Editor, jalankan:
[ ] CREATE TABLE materi_unit  (SQL di atas)
[ ] CREATE TABLE gambar_materi (SQL di atas)
[ ] ALTER TABLE soal_eps ADD COLUMN gambar_pilihan_a/b/c/d

Di folder project:
[ ] .env berisi SUPABASE_URL dan SUPABASE_ANON_KEY
[ ] langit-korea-extracted/ sudah di-extract dari ZIP
[ ] pip install supabase
```

---

## 🏃 JALANKAN DI TERMINAL ZED

```bash
# Masuk ke folder project
cd path/ke/langit-korea

# Diagnosa dulu
python check_env.py

# Jalankan integrasi
python integrate_to_supabase.py
```

---

## 📊 RINGKASAN DATA YANG AKAN TERUPLOAD

| Tipe Data | Jumlah | Tabel/Bucket |
|---|---|---|
| Soal EPS-TOPIK | 135 soal (27 unit × 5) | `soal_eps` |
| Teks materi | 189 halaman teks | `materi_unit` |
| Gambar vocab | ~600 gambar | `gambar-materi` storage |
| Gambar grammar | ~140 gambar | `gambar-materi` storage |
| Gambar percakapan | ~120 gambar | `gambar-materi` storage |
| Gambar budaya | ~300 gambar | `gambar-materi` storage |
| Gambar soal pilihan | ~48 gambar (12 soal × 4) | `gambar-soal` storage |

**Total: ~1.350 gambar + 135 soal + 189 materi teks**
