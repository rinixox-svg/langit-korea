#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script lengkap untuk memperbaiki parsing semua 30 unit (31-60)
Menangani:
1. JSON yang rusak (syntax error)
2. data.json yang belum ada
3. Parsing instruksi di antara soal
4. Generate laporan lengkap
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

print("=== FIX ALL UNITS - LANGIT KOREA ===")
print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

base_dir = Path("../assets/langit-korea-extracted")
output_dir = Path("./langit-korea-json")
output_dir.mkdir(parents=True, exist_ok=True)

# Definisi unit
UNITS = [
    (
        31,
        "unit_31_attire_work_attitude.pdf",
        "복장과 근무 태도",
        "Pakaian dan Sikap Kerja",
    ),
    (
        32,
        "unit_32_use_of_company_facilities.pdf",
        "회사 시설 이용",
        "Penggunaan Fasilitas Perusahaan",
    ),
    (
        33,
        "unit_33_colleague_relationships.pdf",
        "동료와의 관계",
        "Hubungan dengan Rekan Kerja",
    ),
    (
        34,
        "unit_34_sexual_harassment_prevention.pdf",
        "성희롱 및 성추행 예방",
        "Pencegahan Pelecehan Seksual",
    ),
    (35, "unit_35_workplace_management.pdf", "작업장 관리", "Manajemen Tempat Kerja"),
    (36, "unit_36_shipment_management.pdf", "출하 관리", "Manajemen Pengiriman"),
    (37, "unit_37_machine_processing.pdf", "기계 가공", "Pemrosesan Mesin"),
    (38, "unit_38_machine_assembly.pdf", "기계 조립", "Perakitan Mesin"),
    (39, "unit_39_metal_processing.pdf", "금속 가공", "Pengolahan Logam"),
    (
        40,
        "unit_40_plastic_rubber_molding.pdf",
        "플라스틱 고무 성형",
        "Pembentukan Plastik dan Karet",
    ),
    (41, "unit_41_textile_manufacturing.pdf", "섬유 제조", "Manufaktur Tekstil"),
    (42, "unit_42_furniture_making.pdf", "가구 제작", "Pembuatan Furnitur"),
    (43, "unit_43_building_construction.pdf", "건축 시공", "Konstruksi Bangunan"),
    (44, "unit_44_civil_engineering.pdf", "토목 시공", "Teknik Sipil"),
    (45, "unit_45_crop_cultivation.pdf", "농작물 재배", "Budidaya Tanaman"),
    (46, "unit_46_animal_husbry.pdf", "사육 관리", "Peternakan"),
    (
        47,
        "unit_47_coastal_fishing_aquaculture.pdf",
        "연안 어업과 양식",
        "Perikanan dan Budidaya",
    ),
    (48, "unit_48_ship_hull_construction.pdf", "선체 건조", "Konstruksi Lambung Kapal"),
    (
        49,
        "unit_49_mineral_resource_development.pdf",
        "광물 자원 개발 생산",
        "Pengembangan Sumber Daya Mineral",
    ),
    (
        50,
        "unit_50_forest_resource_development.pdf",
        "산림 자원 조성",
        "Pengembangan Sumber Daya Hutan",
    ),
    (51, "unit_51_accommodation_services.pdf", "숙박 서비스", "Layanan Akomodasi"),
    (52, "unit_52_food_preparation.pdf", "음식 조리", "Persiapan Makanan"),
    (
        53,
        "unit_53_industrial_safety_signs.pdf",
        "산업 안전 및 보건 표지",
        "Tanda Keselamatan Industri",
    ),
    (
        54,
        "unit_54_industrial_safety_rules.pdf",
        "산업 안전 및 보건 수칙",
        "Aturan Keselamatan Industri",
    ),
    (
        55,
        "unit_55_safety_hygiene_equipment.pdf",
        "산업 안전 및 위생 장비",
        "Peralatan K3",
    ),
    (
        56,
        "unit_56_industrial_accidents_first_ai.pdf",
        "산업 재해 및 응급 처치",
        "Kecelakaan Industri dan P3K",
    ),
    (57, "unit_57_employment_permit_system.pdf", "고용허가제", "Sistem Izin Kerja G2G"),
    (58, "unit_58_labor_stards_act.pdf", "근로기준법", "UU Ketenagakerjaan Korea"),
    (59, "unit_59_immigration_control_act.pdf", "출입국관리법", "UU Imigrasi Korea"),
    (60, "unit_60_workers_insurance.pdf", "근로자 보험", "Asuransi Pekerja"),
]


def fix_json_file(file_path):
    """Coba perbaiki JSON yang rusak"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Coba parse langsung
        json.loads(content)
        return True
    except json.JSONDecodeError as e:
        print(f"    [!] JSON error: {e}")
        # Coba perbaiki dengan menambahkan comma yang hilang
        # Ini adalah perbaikan sederhana, mungkin perlu diperbaiki manual
        return False


def parse_soal_txt(txt_path, tipe="membaca"):
    """Parse file hal8_soal.txt atau hal9_soal.txt"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return []

    lines = text.split("\n")
    soal_list = []
    current_soal = None
    current_number = None
    instruction_buffer = ""

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header
        if re.match(r"^(읽기|듣기)\s+(READING|LISTENING)", line_stripped):
            continue

        # Detect question number
        match = re.match(r"^(\d+)\.\s*", line_stripped)
        if match:
            # Save previous soal
            if current_soal and current_number:
                if instruction_buffer:
                    current_soal["instruksi"] = instruction_buffer.strip()
                    instruction_buffer = ""
                soal_list.append(current_soal)

            num = int(match.group(1))
            if num > 5:
                break

            current_number = num
            teks = line_stripped[match.end() :].strip()

            current_soal = {
                "nomor": num,
                "tipe": tipe,
                "teks_soal": teks,
                "instruksi": "",
                "pilihan_a": "",
                "pilihan_b": "",
                "pilihan_c": "",
                "pilihan_d": "",
            }
            continue

        if not current_soal:
            continue

        # Detect instruction
        is_instruction = False
        instr_keywords = ["고르십시오", "알맞은", "들고", "읽고", "[", "~"]
        if any(kw in line_stripped for kw in instr_keywords):
            if re.search(r"\[\d+~\d+\]", line_stripped) or any(
                kw in line_stripped for kw in ["고르십시오", "알맞은"]
            ):
                is_instruction = True

        if is_instruction:
            if instruction_buffer:
                instruction_buffer += " " + line_stripped
            else:
                instruction_buffer = line_stripped
            continue

        # Detect choices
        if "①" in line_stripped:
            # Parse all choices
            for i, (sym, key) in enumerate(
                [("①", "a"), ("②", "b"), ("③", "c"), ("④", "d")]
            ):
                if sym in line_stripped:
                    idx = line_stripped.index(sym)
                    rest = line_stripped[idx + 1 :].strip()
                    # Remove other symbols
                    for other_sym in ["①", "②", "③", "④"]:
                        if other_sym in rest:
                            rest = rest[: rest.index(other_sym)].strip()
                    current_soal[f"pilihan_{key}"] = rest
            continue
        elif line_stripped.startswith("②"):
            current_soal["pilihan_b"] = line_stripped[1:].strip()
            continue
        elif line_stripped.startswith("③"):
            current_soal["pilihan_c"] = line_stripped[1:].strip()
            continue
        elif line_stripped.startswith("④"):
            current_soal["pilihan_d"] = line_stripped[1:].strip()
            continue
        else:
            # Continuation of question text
            if current_soal["teks_soal"]:
                current_soal["teks_soal"] += " " + line_stripped
            else:
                current_soal["teks_soal"] = line_stripped

    # Save last soal
    if current_soal and current_number:
        if instruction_buffer:
            current_soal["instruksi"] = instruction_buffer.strip()
        soal_list.append(current_soal)

    return soal_list


def create_or_fix_data_json(unit_num, unit_data):
    """Create or fix data.json for a unit"""
    unit_dir = base_dir / f"unit_{unit_num:02d}"
    data_path = unit_dir / "data.json"

    # Parse soal from txt files
    hal8_path = unit_dir / "teks" / "hal8_soal.txt"
    hal9_path = unit_dir / "teks" / "hal9_soal.txt"

    reading_soal = []
    listening_soal = []

    if hal8_path.exists():
        reading_soal = parse_soal_txt(hal8_path, "membaca")
        # Add IDs
        for s in reading_soal:
            s["id"] = f"u{unit_num}_m{s['nomor']}"
            s["jawaban"] = ""  # Will be filled from appendix-answers later
            s["audio_teks"] = ""
            s["ada_gambar_pilihan"] = False
            s["gambar_pilihan"] = {}
            s["akses"] = "free"

    if hal9_path.exists():
        listening_soal = parse_soal_txt(hal9_path, "mendengarkan")
        for s in listening_soal:
            s["id"] = f"u{unit_num}_l{s['nomor']}"
            s["jawaban"] = ""
            s["audio_teks"] = ""
            s["ada_gambar_pilihan"] = False
            s["gambar_pilihan"] = {}
            s["akses"] = "free"

    # Create data structure
    data = {
        "unit": unit_num,
        "title_ko": unit_data[2],
        "title_id": unit_data[3],
        "file": unit_data[1],
        "total_halaman": 10,
        "soal": reading_soal + listening_soal,
    }

    # Save
    try:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, len(reading_soal), len(listening_soal)
    except Exception as e:
        print(f"    [!] Error saving: {e}")
        return False, 0, 0


# Main loop
success_count = 0
failed_units = []
laporan_detail = {}

for unit_info in UNITS:
    unit_num = unit_info[0]
    print(f"[{unit_num - 30}/30] Unit {unit_num:02d}...", end=" ")

    unit_dir = base_dir / f"unit_{unit_num:02d}"
    data_path = unit_dir / "data.json"

    # Check if unit directory exists
    if not unit_dir.exists():
        print("directory tidak ada")
        failed_units.append(unit_num)
        continue

    # Check txt files
    hal8_exists = (unit_dir / "teks" / "hal8_soal.txt").exists()
    hal9_exists = (unit_dir / "teks" / "hal9_soal.txt").exists()

    if not hal8_exists and not hal9_exists:
        print("txt files tidak ada")
        failed_units.append(unit_num)
        continue

    # Create or fix data.json
    success, r_count, l_count = create_or_fix_data_json(unit_num, unit_info)

    if success:
        print(f"✓ (R:{r_count}, L:{l_count})")
        success_count += 1
        laporan_detail[unit_num] = {"reading": r_count, "listening": l_count}
    else:
        print("✗ (error)")
        failed_units.append(unit_num)

print(f"\n=== LAPORAN AKHIR ===")
print(f"Berhasil: {success_count}/30")
print(f"Gagal: {len(failed_units)}")
if failed_units:
    print(f"  Unit gagal: {failed_units}")

# Save laporan
laporan = {
    "waktu": datetime.now().isoformat(),
    "total_unit": 30,
    "berhasil": success_count,
    "gagal": failed_units,
    "detail": laporan_detail,
}

laporan_path = output_dir / "laporan_fix_all.json"
with open(laporan_path, "w", encoding="utf-8") as f:
    json.dump(laporan, f, ensure_ascii=False, indent=2)

print(f"\nLaporan: {laporan_path}")
print("\n=== SELESAI ===")
