import fitz
import json
import os
import sys
import re
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
PDF_DIR = "pdf_modul"
OUTPUT_DIR = "data"
UNIT_RANGE = range(31, 61)
DEBUG = False

HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}


def get_pdf_file(unit_num):
    name_map = {
        31: "unit_31_attire_work_attitude.pdf",
        32: "unit_32_use_of_company_facilities.pdf",
        33: "unit_33_colleague_relationships.pdf",
        34: "unit_34_sexual_harassment_prevention.pdf",
        35: "unit_35_workplace_management.pdf",
        36: "unit_36_shipment_management.pdf",
        37: "unit_37_machine_processing.pdf",
        38: "unit_38_machine_assembly.pdf",
        39: "unit_39_metal_processing.pdf",
        40: "unit_40_plastic_rubber_molding.pdf",
        41: "unit_41_textile_manufacturing.pdf",
        42: "unit_42_furniture_making.pdf",
        43: "unit_43_building_construction.pdf",
        44: "unit_44_civil_engineering.pdf",
        45: "unit_45_crop_cultivation.pdf",
        46: "unit_46_animal_husbry.pdf",
        47: "unit_47_coastal_fishing_aquaculture.pdf",
        48: "unit_48_ship_hull_construction.pdf",
        49: "unit_49_mineral_resource_development.pdf",
        50: "unit_50_forest_resource_development.pdf",
        51: "unit_51_accommodation_services.pdf",
        52: "unit_52_food_preparation.pdf",
        53: "unit_53_industrial_safety_signs.pdf",
        54: "unit_54_industrial_safety_rules.pdf",
        55: "unit_55_safety_hygiene_equipment.pdf",
        56: "unit_56_industrial_accidents_first_ai.pdf",
        57: "unit_57_employment_permit_system.pdf",
        58: "unit_58_labor_stards_act.pdf",
        59: "unit_59_immigration_control_act.pdf",
        60: "unit_60_workers_insurance.pdf",
    }
    return os.path.join(PDF_DIR, name_map.get(unit_num, f"unit_{unit_num}.pdf"))


def get_pdf_pages(pdf_path, unit_num):
    pages = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        end_page = min(9, total_pages)
        for i in range(0, end_page):
            text = doc[i].get_text()
            pages.append(text)
        for _ in range(len(pages), 9):
            pages.append("")
        doc.close()
    except FileNotFoundError:
        pages = [""] * 9
    return pages


def parse_vocab(text):
    items = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        has_korean = bool(re.search(r'[가-힣]', line))
        has_english = bool(re.search(r'[a-zA-Z]', line))
        
        if has_korean and has_english:
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 2:
                korean_part = parts[0].strip()
                indo_part = ' '.join(parts[1:]).strip()
                
                if korean_part and indo_part:
                    items.append({
                        "korean": korean_part,
                        "indonesia": indo_part
                    })
                i += 1
                continue
        
        if has_korean and not has_english and i + 1 < len(lines):
            next_line = lines[i + 1]
            if not re.search(r'[가-힣]', next_line):
                korean_part = line.strip()
                indo_part = next_line.strip()
                
                if korean_part and indo_part:
                    items.append({
                        "korean": korean_part,
                        "indonesia": indo_part
                    })
                i += 2
                continue
        
        if has_korean:
            korean_part = line.strip()
            j = i + 1
            while j < len(lines) and not re.search(r'[가-힣]', lines[j]):
                j += 1
            
            if j > i + 1:
                indo_parts = [lines[k] for k in range(i + 1, j)]
                indo_part = ' '.join(indo_parts).strip()
                
                if korean_part and indo_part:
                    items.append({
                        "korean": korean_part,
                        "indonesia": indo_part
                    })
                i = j
                continue
        
        i += 1
    
    return items


def parse_grammar(text):
    items = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        has_korean = bool(re.search(r'[가-힣]', line))
        
        if has_korean and i + 1 < len(lines):
            next_line = lines[i + 1]
            has_english_next = bool(re.search(r'[a-zA-Z]', next_line))
            
            if has_english_next:
                items.append({
                    "pattern": line.strip(),
                    "explanation": next_line.strip()
                })
                i += 2
                continue
        
        i += 1
    
    return items


def parse_conversation(text):
    dialogues = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        speaker_match = re.match(r'^([가-힣a-zA-Z\s]+)[:：]\s*(.+)$', line)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            text_content = speaker_match.group(2).strip()
            
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                speaker_check = re.match(r'^([가-힣a-zA-Z\s]+)[:：]\s*(.+)$', next_line)
                if speaker_check:
                    break
                text_content += ' ' + next_line
                j += 1
            
            if text_content:
                dialogues.append({
                    "speaker": speaker,
                    "text": text_content.strip()
                })
            i = j
            continue
        
        i += 1
    
    return dialogues


def parse_budaya(text):
    info = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        has_korean_title = bool(re.search(r'^[가-힣]{2,4}$', line)) and i + 1 < len(lines)
        
        if has_korean_title:
            next_line = lines[i + 1]
            if re.search(r'[가-힣]', next_line):
                title = line.strip()
                content = next_line.strip()
                
                j = i + 2
                while j < len(lines) and not re.match(r'^[가-힣]{2,4}$', lines[j]):
                    content += ' ' + lines[j].strip()
                    j += 1
                
                if title and content:
                    info.append({
                        "title": title,
                        "content": content.strip()
                    })
                i = j
                continue
        
        i += 1
    
    return info


def parse_unit_pages(pages):
    return {
        "vocab1": parse_vocab(pages[0]) if len(pages) > 0 else [],
        "grammar1": parse_grammar(pages[1]) if len(pages) > 1 else [],
        "conversation1": parse_conversation(pages[2]) if len(pages) > 2 else [],
        "vocab2": parse_vocab(pages[3]) if len(pages) > 3 else [],
        "grammar2": parse_grammar(pages[4]) if len(pages) > 4 else [],
        "conversation2": parse_conversation(pages[5]) if len(pages) > 5 else [],
        "budaya": parse_budaya(pages[6]) if len(pages) > 6 else []
    }


def upload_to_latihan_v2(unit_num, data):
    url = f"{SUPABASE_URL}/rest/v1/latihan_v2"
    
    payload = {
        "unit": unit_num,
        "vocab1": json.dumps(data["vocab1"], ensure_ascii=False),
        "grammar1": json.dumps(data["grammar1"], ensure_ascii=False),
        "conversation1": json.dumps(data["conversation1"], ensure_ascii=False),
        "vocab2": json.dumps(data["vocab2"], ensure_ascii=False),
        "grammar2": json.dumps(data["grammar2"], ensure_ascii=False),
        "conversation2": json.dumps(data["conversation2"], ensure_ascii=False),
        "budaya": json.dumps(data["budaya"], ensure_ascii=False)
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        if response.status_code in [200, 201]:
            return True, "created"
        elif response.status_code == 400:
            d = response.json() if response.text else {}
            if d.get("code") == "PGRST204":
                return False, "Table latihan_v2 not found"
            return False, f"HTTP 400: {d.get('message', '')[:80]}"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def main():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Error: SET ENV VARIABLES FIRST")
        print("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        sys.exit(1)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Extracting units 31-60 from PDF files")
    print("=" * 50)
    
    results = {"success": 0, "failed": 0, "skipped": 0}
    all_data = []
    
    for unit_num in UNIT_RANGE:
        pdf_file = get_pdf_file(unit_num)
        print(f"\nProcessing Unit {unit_num}...")
        print(f"  File: {pdf_file}")
        
        pages = get_pdf_pages(pdf_file, unit_num)
        parsed = parse_unit_pages(pages)
        
        vocab_count = len(parsed["vocab1"]) + len(parsed["vocab2"])
        grammar_count = len(parsed["grammar1"]) + len(parsed["grammar2"])
        conv_count = len(parsed["conversation1"]) + len(parsed["conversation2"])
        budaya_count = len(parsed["budaya"])
        
        print(f"  - Vocab: {vocab_count}")
        print(f"  - Grammar: {grammar_count}")
        print(f"  - Conversation: {conv_count}")
        print(f"  - Budaya: {budaya_count}")
        
        if DEBUG and vocab_count > 0:
            print(f"    Sample vocab: {parsed['vocab1'][0]}")
        if DEBUG and grammar_count > 0:
            print(f"    Sample grammar: {parsed['grammar1'][0]}")
        
        total_items = vocab_count + grammar_count + conv_count + budaya_count
        
        if total_items == 0:
            print(f"  ! Tidak ada konten yang bisa di-ekstrak")
            results["skipped"] += 1
            continue
        
        row = {
            "unit": unit_num,
            "vocab1": parsed["vocab1"],
            "grammar1": parsed["grammar1"],
            "conversation1": parsed["conversation1"],
            "vocab2": parsed["vocab2"],
            "grammar2": parsed["grammar2"],
            "conversation2": parsed["conversation2"],
            "budaya": parsed["budaya"]
        }
        all_data.append(row)
        
        with open(os.path.join(OUTPUT_DIR, f"unit_{unit_num}.json"), "w", encoding="utf-8") as f:
            json.dump(row, f, ensure_ascii=False, indent=2)
        
        success, msg = upload_to_latihan_v2(unit_num, parsed)
        
        if success:
            print(f"  Uploaded ({msg})")
            results["success"] += 1
        else:
            print(f"  Saved to file: {msg}")
            results["failed"] += 1
    
    combined_file = os.path.join(OUTPUT_DIR, "all_units.json")
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"Done! Uploaded: {results['success']}, Saved to file: {results['failed']}, Skipped: {results['skipped']}")
    print(f"\nData saved to: {OUTPUT_DIR}/")
    print(f"  - unit_31.json ... unit_60.json (per unit)")
    print(f"  - all_units.json (kombinasi semua unit)")
    print("\nTo upload to Supabase:")
    print("1. Go to Supabase Dashboard > SQL Editor")
    print("2. Run SQL to create latihan_v2 table")
    print("3. Import data from data/all_units.json\n")


if __name__ == "__main__":
    main()
