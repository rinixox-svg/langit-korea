#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("SUPABASE_URL atau SUPABASE_ANON_KEY tidak ditemukan di .env")
        exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("Koneksi Supabase OK")
except ImportError:
    print(
        "Library supabase belum diinstall. Jalankan: pip install supabase python-dotenv"
    )
    exit(1)

EXTRACTED_DIR = Path("./langit-korea-extracted")


def upload_gambar(local_path, storage_path, bucket):
    if not local_path.exists():
        return None

    ext = local_path.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    else:
        mime = "image/png"

    with open(local_path, "rb") as f:
        data = f.read()

    try:
        client.storage.from_(bucket).upload(
            path=storage_path,
            file=data,
            file_options={"content-type": mime, "upsert": "true"},
        )
    except Exception as e:
        if "409" in str(e) or "already exists" in str(e).lower():
            pass
        else:
            raise e

    url_obj = client.storage.from_(bucket).get_public_url(storage_path)
    return url_obj


def bersih_teks(t):
    if not t:
        return ""
    t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(t))
    return re.sub(r"\s+", " ", t).strip()


def process_unit(unit_dir):
    data_path = unit_dir / "data.json"
    if not data_path.exists():
        print(f"  {unit_dir.name}: data.json tidak ada, skip")
        return None

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    unit_num = data["unit"]
    title_ko = data.get("title_ko", "")
    title_id = data.get("title_id", "")

    print(f"\nUnit {unit_num}: {title_id}")

    result = {"unit": unit_num, "materi_ok": 0, "gambar_ok": 0, "soal_ok": 0}

    # 1. UPLOAD GAMBAR MATERI
    hal_map = {
        "hal1_vocab": ("vocab", 1),
        "hal2_grammar": ("grammar", 1),
        "hal3_conv": ("conversation", 1),
        "hal4_vocab": ("vocab", 2),
        "hal5_grammar": ("grammar", 2),
        "hal6_conv": ("conversation", 2),
        "hal7_culture": ("culture", 1),
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
                if url:
                    client.table("gambar_materi").upsert(
                        {
                            "unit": unit_num,
                            "kategori": kategori,
                            "sub": sub,
                            "urutan": urutan,
                            "storage_url": url,
                            "lebar": 0,
                            "tinggi": 0,
                            "akses": "free",
                        }
                    ).execute()
                    result["gambar_ok"] += 1
                    time.sleep(0.03)
            except Exception as e:
                print(f"    {img_path.name}: {str(e)[:60]}")

    print(f"  Gambar materi: {result['gambar_ok']} terupload")

    # 2. UPLOAD TEKS MATERI
    teks_map = {
        "hal1_vocab.txt": ("vocab", 1),
        "hal2_grammar.txt": ("grammar", 1),
        "hal3_conv.txt": ("conversation", 1),
        "hal4_vocab.txt": ("vocab", 2),
        "hal5_grammar.txt": ("grammar", 2),
        "hal6_conv.txt": ("conversation", 2),
        "hal7_culture.txt": ("culture", 1),
    }

    for fname, (kategori, sub) in teks_map.items():
        txt_path = unit_dir / "teks" / fname
        if not txt_path.exists():
            continue
        teks = txt_path.read_text(encoding="utf-8").strip()
        if not teks:
            continue

        try:
            client.table("materi_unit").upsert(
                {
                    "unit": unit_num,
                    "title_ko": title_ko,
                    "title_id": title_id,
                    "kategori": kategori,
                    "sub": sub,
                    "teks": teks,
                    "akses": "free",
                }
            ).execute()
            result["materi_ok"] += 1
        except Exception as e:
            print(f"    Materi {fname}: {str(e)[:60]}")

    print(f"  Teks materi: {result['materi_ok']} tersimpan")

    # 3. UPLOAD SOAL
    soal_list = data.get("soal", [])
    soal_ok = 0

    for soal in soal_list:
        gambar_url = {}
        if soal.get("ada_gambar_pilihan") and soal.get("gambar_pilihan"):
            for huruf, rel_path in soal["gambar_pilihan"].items():
                img_path = unit_dir / rel_path
                if img_path.exists():
                    storage_path = f"soal/unit_{unit_num:02d}/{img_path.name}"
                    try:
                        url = upload_gambar(img_path, storage_path, "gambar-soal")
                        gambar_url[huruf] = url
                    except Exception as e:
                        print(f"    Gambar soal {huruf}: {str(e)[:60]}")

        # Paksa nilai tipe sesuai constraint (membaca/mendengarkan)
        tipe_raw = soal.get("tipe", "").lower()
        if "baca" in tipe_raw:
            tipe_final = "membaca"
        elif "dengar" in tipe_raw or "listening" in tipe_raw:
            tipe_final = "mendengarkan"
        else:
            tipe_final = "membaca"  # default

        # Paksa nilai akses sesuai constraint (free/premium/review)
        akses_raw = soal.get("akses", "free")
        if akses_raw not in ["free", "premium", "review"]:
            akses_final = "free"  # default
        else:
            akses_final = akses_raw

                # Paksa nilai sesuai constraint database
        # 1. tipe: hanya 'membaca' atau 'mendengarkan'
        tipe_raw = soal.get("tipe", "").lower()
        if "baca" in tipe_raw:
            tipe_final = "membaca"
        elif "dengar" in tipe_raw or "listening" in tipe_raw:
            tipe_final = "mendengarkan"
        else:
            tipe_final = "membaca"  # default
        
        # 2. akses: hanya 'free', 'premium', atau 'review'
        akses_raw = soal.get("akses", "free")
        if akses_raw not in ["free", "premium", "review"]:
            akses_final = "free"  # default
        else:
            akses_final = akses_raw
        
        # 3. jawaban: hanya a/b/c/d
        jawaban_raw = soal.get("jawaban", "?").lower()
        if jawaban_raw not in ["a", "b", "c", "d"]:
            jawaban_final = "a"  # placeholder
        else:
            jawaban_final = jawaban_raw
        
        row = {
            "unit": unit_num,
            "tipe": tipe_final,  # PASTI SESUAI constraint
            "teks_soal": bersih_teks(soal.get("teks_soal", "")),
            "pilihan_a": bersih_teks(soal.get("pilihan_a", "")),
            "pilihan_b": bersih_teks(soal.get("pilihan_b", "")),
            "pilihan_c": bersih_teks(soal.get("pilihan_c", "")),
            "pilihan_d": bersih_teks(soal.get("pilihan_d", "")),
            "jawaban": jawaban_final,  # PASTI SESUAI
            "audio_teks": bersih_teks(soal.get("audio_teks", "")),
            "ada_gambar_pilihan": bool(soal.get("ada_gambar_pilihan")),
            "gambar_pilihan_a": gambar_url.get("a"),
            "gambar_pilihan_b": gambar_url.get("b"),
            "gambar_pilihan_c": gambar_url.get("c"),
            "gambar_pilihan_d": gambar_url.get("d"),
            "akses": akses_final,  # PASTI SESUAI constraint
        }


        if not row["teks_soal"]:
            continue

        if row["jawaban"] == "?":
            row["jawaban"] = "a"
            row["akses"] = "review"

        try:
            client.table("soal_eps").upsert(row).execute()
            soal_ok += 1
            result["soal_ok"] += 1
            time.sleep(0.03)
        except Exception as e:
            print(f"    Soal {soal.get('id')}: {str(e)[:80]}")

    print(f"  Soal: {soal_ok}/{len(soal_list)} terupload")

    return result


def main():
    print("=" * 55)
    print("INTEGRASI LANGIT KOREA KE SUPABASE")
    print("=" * 55)

    if not EXTRACTED_DIR.exists():
        print(f"Direktori {EXTRACTED_DIR} tidak ditemukan.")
        print("Pastikan folder 'langit-korea-extracted/' ada di root project.")
        exit(1)

    unit_dirs = sorted(
        [
            d
            for d in EXTRACTED_DIR.iterdir()
            if d.is_dir()
            and d.name.startswith("unit_")
            and not d.name.startswith("unit_appendix")
        ]
    )

    print(f"\n{len(unit_dirs)} unit ditemukan.\n")

    total_soal_ok = 0
    total_materi_ok = 0
    total_gambar_ok = 0

    for unit_dir in unit_dirs:
        result = process_unit(unit_dir)
        if result:
            total_soal_ok += result["soal_ok"]
            total_materi_ok += result["materi_ok"]
            total_gambar_ok += result["gambar_ok"]

    print("\n" + "=" * 55)
    print("LAPORAN INTEGRASI SELESAI")
    print("=" * 55)
    print(f"Total soal    : {total_soal_ok}")
    print(f"Total materi  : {total_materi_ok}")
    print(f"Total gambar  : {total_gambar_ok}")
    print(f"\nCek di Supabase Dashboard -> Table Editor")
    print("=" * 55)


if __name__ == "__main__":
    main()
