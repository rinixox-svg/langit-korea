#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk extract 5 soal listening + 5 teks audio dari hal9_soal.txt
dan match dengan gambar di folder images/
"""

import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv

try:
    from supabase import create_client
except ImportError as e:
    print(f"Error: {e}")
    exit(1)

load_dotenv()

EXTRACTED_DIR = Path("assets/langit-korea-extracted")
OUTPUT_JSON = "soal_listening_complete.json"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("SUPABASE_URL atau SUPABASE_ANON_KEY tidak ditemukan")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
print("Koneksi Supabase OK\n")

def parse_hal9_soal(unit_num):
    """Parse hal9_soal.txt untuk 5 soal + 5 teks audio"""
    txt_path = EXTRACTED_DIR / f"unit_{unit_num:02d}" / "teks" / "hal9_soal.txt"
    
    if not txt_path.exists():
        print(f"Unit {unit_num}: {txt_path.name} tidak ditemukan")
        return []
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split antara soal dan teks audio
    # Teks audio biasanya dimulai dengan "듣기지문" atau "지문"
    parts = re.split(r'지문|듣기지문', text)
    
    soal_text = parts[0] if len(parts) > 0 else text
    audio_text = parts[1] if len(parts) > 1 else ""
    
    # Parse 5 soal
    soal_list = []
    lines = soal_text.split('\n')
    
    current_soal = None
    current_number = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Deteksi nomor soal (1. 2. 3. 4. 5.)
        match = re.match(r'^(\d+)\.\s*', line)
        if match:
            # Simpan soal sebelumnya
            if current_soal and current_number:
                soal_list.append(current_soal)
            
            current_number = int(match.group(1))
            if current_number > 5:
                break
            
            current_soal = {
                "id": f"u{unit_num}_l{current_number}",
                "unit": unit_num,
                "nomor": current_number,
                "tipe": "mendengarkan",
                "teks_soal": "",
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
                "jawaban": "",
                "audio_teks": "",
                "ada_gambar_pilihan": False,
                "gambar_pilihan_a": None,
                "gambar_pilihan_b": None,
                "gambar_pilihan_c": None,
                "gambar_pilihan_d": None,
                "akses": "free" if unit_num <= 18 else "premium"
            }
            continue
        
        if not current_soal:
            continue
        
        # Deteksi teks soal
        if not current_soal["teks_soal"]:
            if line and not line.startswith(('①', '②', '③', '④')):
                current_soal["teks_soal"] = line
                continue
        
        # Deteksi pilihan
        if line.startswith('①'):
            current_soal["pilihan_a"] = line[1:].strip()
        elif line.startswith('②'):
            current_soal["pilihan_b"] = line[1:].strip()
        elif line.startswith('③'):
            current_soal["pilihan_c"] = line[1:].strip()
        elif line.startswith('④'):
            current_soal["pilihan_d"] = line[1:].strip()
    
    # Simpan soal terakhir
    if current_soal and current_number:
        soal_list.append(current_soal)
    
    # Parse teks audio (5 teks)
    if audio_text:
        # Bersihkan teks audio
        audio_text = re.sub(r'\d+\.\s*', '\n###SPLIT###', audio_text)
        audio_parts = [p.strip() for p in audio_text.split('###SPLIT###') if p.strip()]
        
        for i, soal in enumerate(soal_list):
            if i < len(audio_parts):
                soal["audio_teks"] = audio_parts[i]
    
    return soal_list[:5]

def match_gambar(unit_num, soal_list):
    """Match gambar soal listening dari folder images/"""
    images_dir = EXTRACTED_DIR / f"unit_{unit_num:02d}" / "images"
    
    if not images_dir.exists():
        return soal_list
    
    for soal in soal_list:
        nomor = soal["nomor"]
        
        # Cek gambar untuk pilihan (jika ada 4 gambar terpisah)
        has_any_image = False
        for huruf in ['a', 'b', 'c', 'd']:
            for ext in ['.jpeg', '.jpg', '.png']:
                img_name = f"u{unit_num:02d}_h9_soal_listening_{nomor:02d}{ext}"
                img_path = images_dir / img_name
                if img_path.exists():
                    soal[f"gambar_pilihan_{huruf}"] = str(img_path)
                    has_any_image = True
                    break
        
        # Cek jika ada gambar tunggal untuk soal
        if has_any_image:
            soal["ada_gambar_pilihan"] = True
    
    return soal_list

def load_jawaban():
    """Load jawaban dari jawaban_all.json"""
    jawaban_path = EXTRACTED_DIR / "jawaban_all.json"
    if jawaban_path.exists():
        with open(str(jawaban_path), 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def main():
    print("=" * 60)
    print("EKSTRAKSI 5 SOAL + 5 TEKS AUDIO PER UNIT")
    print("=" * 60)
    
    jawaban_data = load_jawaban()
    print(f"Jawaban: {len(jawaban_data)} unit\n")
    
    all_soal = []
    total_uploaded = 0
    
    for unit_num in range(31, 61):
        print(f"Unit {unit_num:02d}: ", end='', flush=True)
        
        # Parse hal9_soal.txt
        soal_list = parse_hal9_soal(unit_num)
        
        if not soal_list:
            print("GAGAL parse")
            continue
        
        # Match gambar
        soal_list = match_gambar(unit_num, soal_list)
        
        # Update jawaban
        mendengarkan_jawaban = jawaban_data.get(str(unit_num), {}).get("mendengarkan", {})
        for soal in soal_list:
            nomor = soal["nomor"]
            if str(nomor) in mendengarkan_jawaban:
                soal["jawaban"] = mendengarkan_jawaban[str(nomor)]
        
        print(f"{len(soal_list)} soal")
        all_soal.extend(soal_list)
    
    # Simpan ke JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_soal, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {len(all_soal)} soal listening (30 unit x 5 soal)")
    print(f"File: {OUTPUT_JSON}")
    print("=" * 60)

if __name__ == "__main__":
    main()
