#!/usr/bin/env python3
def parse_listening_text(text, unit_num):
    """Parse teks listening - hanya ambil 5 soal pertama"""
    soal_list = []
    lines = text.split('\n')
    
    current_soal = None
    current_number = None
    soal_count = 0
    
    for line in lines:
        line = line.strip()
        
        # Stop jika sudah dapat 5 soal
        if soal_count >= 5:
            break
        
        # Deteksi nomor soal (1. 2. 3. 4. 5.)
        match = re.match(r'^(\d+)\.\s*$', line)
        if match:
            # Simpan soal sebelumnya
            if current_soal and current_number:
                soal_list.append(current_soal)
                soal_count += 1
            
            if soal_count >= 5:
                break
            
            current_number = int(match.group(1))
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
                "gambar_pilihan": {},
                "akses": "free" if unit_num <= 18 else "premium"
            }
            continue
        
        # Deteksi teks soal
        if current_soal and not current_soal["teks_soal"]:
            if line and not line.startswith(('①', '②', '③', '④')):
                current_soal["teks_soal"] = line
                continue
        
        # Deteksi pilihan jawaban
        if line.startswith('①'):
            current_soal["pilihan_a"] = line[1:].strip()
        elif line.startswith('②'):
            current_soal["pilihan_b"] = line[1:].strip()
        elif line.startswith('③'):
            current_soal["pilihan_c"] = line[1:].strip()
        elif line.startswith('④'):
            current_soal["pilihan_d"] = line[1:].strip()
    
    # Simpan soal terakhir
    if current_soal and current_number and soal_count < 5:
        soal_list.append(current_soal)
    
    return soal_list[:5]  # Pastikan maksimal 5
