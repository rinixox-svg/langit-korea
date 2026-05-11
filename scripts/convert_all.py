import os
import json
from pypdf import PdfReader # Ganti pymupdf menjadi pypdf

# Konfigurasi
PDF_FOLDER = "pdf_modul"  # Pastikan folder ini ada di root project
OUTPUT_JSON = "soal_eps.json"

def extract_text_from_pdf(pdf_path):
    """Fungsi sederhana untuk extract teks dari PDF"""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error membaca {pdf_path}: {e}")
        return ""

def main():
    all_data = []
    
    # Cek folder PDF
    if not os.path.exists(PDF_FOLDER):
        print(f"Folder '{PDF_FOLDER}' tidak ditemukan. Buat folder tersebut dan letakkan PDF di sana.")
        return

    # Loop semua file PDF (Asumsi nama: unit_31.pdf, unit_32.pdf, dst)
    for i in range(31, 61): # Unit 31 sampai 60
        pdf_file = os.path.join(PDF_FOLDER, f"unit_{i}.pdf")
        
        if os.path.exists(pdf_file):
            print(f"Memproses {pdf_file}...")
            text = extract_text_from_pdf(pdf_file)
            
            # Contoh data (Nanti diganti logic parsing yang sesungguhnya)
            all_data.append({
                "id": f"u{i}_r1",
                "unit": i,
                "nomor": 1,
                "tipe": "membaca",
                "teks_soal": text[:200], # Ambil 200 karakter pertama sebagai contoh
                "pilihan_a": "Contoh A",
                "jawaban_benar": "a",
                "akses": "free" if i <= 18 else "premium"
            })
        else:
            print(f"File {pdf_file} tidak ditemukan, lewati.")

    # Simpan ke JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"Selesai! {len(all_data)} data disimpan ke {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
