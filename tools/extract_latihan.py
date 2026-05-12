import os
import fitz  # PyMuPDF
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")

def extract_text_from_page(doc, page_num):
    """Extract text from a specific page (0-indexed)"""
    if page_num < len(doc):
        page = doc.load_page(page_num)
        return page.get_text()
    return ""

def process_unit_pdf(pdf_path, unit_number):
    """Process a single unit PDF and return data ready for Supabase"""
    doc = fitz.open(pdf_path)
    
    # Extract text from pages 1-9 (0-indexed: 0-8)
    pages_text = []
    for i in range(min(9, len(doc))):  # Get up to 9 pages
        text = extract_text_from_page(doc, i)
        pages_text.append(text.strip())
    
    # Map to fields according to specification
    # We need at least 7 pages for the mapping
    if len(pages_text) >= 7:
        data = {
            "unit": unit_number,
            "vocab1": json.dumps(pages_text[0]) if len(pages_text) > 0 else json.dumps(""),
            "grammar1": json.dumps(pages_text[1]) if len(pages_text) > 1 else json.dumps(""),
            "conversation1": json.dumps(pages_text[2]) if len(pages_text) > 2 else json.dumps(""),
            "vocab2": json.dumps(pages_text[3]) if len(pages_text) > 3 else json.dumps(""),
            "grammar2": json.dumps(pages_text[4]) if len(pages_text) > 4 else json.dumps(""),
            "conversation2": json.dumps(pages_text[5]) if len(pages_text) > 5 else json.dumps(""),
            "budaya": json.dumps(pages_text[6]) if len(pages_text) > 6 else json.dumps(""),
        }
        return data
    else:
        print(f"Warning: Unit {unit_number} PDF has less than 7 pages ({len(pages_text)} pages)")
        # Still return what we have, padding with empty strings
        data = {
            "unit": unit_number,
            "vocab1": json.dumps(pages_text[0]) if len(pages_text) > 0 else json.dumps(""),
            "grammar1": json.dumps(pages_text[1]) if len(pages_text) > 1 else json.dumps(""),
            "conversation1": json.dumps(pages_text[2]) if len(pages_text) > 2 else json.dumps(""),
            "vocab2": json.dumps(pages_text[3]) if len(pages_text) > 3 else json.dumps(""),
            "grammar2": json.dumps(pages_text[4]) if len(pages_text) > 4 else json.dumps(""),
            "conversation2": json.dumps(pages_text[5]) if len(pages_text) > 5 else json.dumps(""),
            "budaya": json.dumps(pages_text[6]) if len(pages_text) > 6 else json.dumps(""),
        }
        return data

def upload_to_supabase(data):
    """Upload data to Supabase latihan_interaktif table"""
    url = f"{SUPABASE_URL}/rest/v1/latihan_interaktif"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"Successfully uploaded unit {data['unit']}")
        return response.json()
    else:
        print(f"Failed to upload unit {data['unit']}: {response.status_code} - {response.text}")
        return None

def main():
    # Path to unit PDFs
    assets_dir = Path("assets/langit-korea-modules")
    
    if not assets_dir.exists():
        print(f"Assets directory not found: {assets_dir}")
        print("Please ensure the PDF files are in assets/langit-korea-modules/")
        return
    
    # Process units 31-60
    processed_count = 0
    for unit_num in range(31, 61):
        # Look for PDF file matching unit pattern
        pdf_pattern = f"unit_{unit_num}_*.pdf"
        pdf_files = list(assets_dir.glob(pdf_pattern))
        
        if not pdf_files:
            print(f"No PDF found for unit {unit_num} with pattern {pdf_pattern}")
            continue
        
        pdf_path = pdf_files[0]
        print(f"Processing unit {unit_num}: {pdf_path.name}")
        
        try:
            # Extract and process data
            data = process_unit_pdf(pdf_path, unit_num)
            
            # Upload to Supabase
            result = upload_to_supabase(data)
            
            if result:
                print(f"Unit {unit_num} processed successfully")
                processed_count += 1
            else:
                print(f"Failed to upload unit {unit_num}")
                
        except Exception as e:
            print(f"Error processing unit {unit_num}: {str(e)}")
            continue
    
    print(f"\nProcessing complete. Successfully processed {processed_count} units.")
    if processed_count < 30:
        print("Note: If you see 'Could not find column' errors, you may need to run the setup_latihan.sql script first.")
        print("The script creates the latihan_interaktif table with the expected schema.")

if __name__ == "__main__":
    main()