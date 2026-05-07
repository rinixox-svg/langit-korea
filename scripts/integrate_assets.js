const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
const AdmZip = require('adm-zip');

// === KONFIGURASI SUPABASE ===
// Baca dari js/supabase-config.js
const configPath = path.join(__dirname, '..', 'js', 'supabase-config.js');
let supabaseUrl, supabaseKey;

try {
    const configContent = fs.readFileSync(configPath, 'utf8');
    const urlMatch = configContent.match(/SUPABASE_URL\s*=\s*["']([^"']+)["']/);
    const keyMatch = configContent.match(/SUPABASE_ANON_KEY\s*=\s*["']([^"']+)["']/);

    if (urlMatch && keyMatch) {
        supabaseUrl = urlMatch[1];
        supabaseKey = keyMatch[1];
        console.log('✅ Ditemukan Supabase URL:', supabaseUrl);
    } else {
        console.error('❌ Tidak ditemukan kredensial di js/supabase-config.js');
        process.exit(1);
    }
} catch (err) {
    console.error('❌ Gagal baca config:', err.message);
    process.exit(1);
}

// Inisialisasi Supabase
const supabase = createClient(supabaseUrl, supabaseKey);
console.log('✅ Supabase client initialized');

// === 1. UPLOAD GAMBAR KE STORAGE ===
async function uploadImages() {
    console.log('\n=== MENGUPLOAD GAMBAR KE STORAGE ===');
    const imagesDir = path.join(__dirname, '..', 'assets', 'langit-korea-images');

    if (!fs.existsSync(imagesDir)) {
        console.log('❌ Direktori', imagesDir, 'tidak ditemukan');
        return;
    }

    const files = fs.readdirSync(imagesDir).filter(f =>
        f.toLowerCase().endsWith('.jpeg') || f.toLowerCase().endsWith('.jpg') || f.toLowerCase().endsWith('.png')
    );
    console.log(`Ditemukan ${files.length} file gambar`);

    for (let i = 0; i < files.length; i++) {
        const filename = files[i];
        const filePath = path.join(imagesDir, filename);

        try {
            const fileBuffer = fs.readFileSync(filePath);
            const contentType = filename.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';

            const { data, error } = await supabase.storage
                .from('images')
                .upload(filename, fileBuffer, {
                    contentType: contentType,
                    upsert: true
                });

            if (error) {
                console.error(`  ❌ Gagal upload ${filename}:`, error.message);
            } else {
                if (i % 10 === 0) {
                    console.log(`  ✅ Uploaded ${i+1}/${files.length}: ${filename}`);
                }
            }
        } catch (err) {
            console.error(`  ❌ Gagal upload ${filename}:`, err.message);
        }
    }
    console.log(`✅ Selesai upload gambar (${files.length} file)`);
}

// === 2. EXTRACT AUDIO ZIP DAN UPLOAD KE STORAGE ===
async function uploadAudioFromZip() {
    console.log('\n=== MENGEXTRACT AUDIO DARI ZIP DAN UPLOAD ===');
    const zipFiles = [
        path.join(__dirname, '..', 'assets', 'EPS-TOPIK_textbook1_listen.zip'),
        path.join(__dirname, '..', 'assets', 'EPS-TOPIK_textbook2_listen.zip')
    ];

    for (const zipPath of zipFiles) {
        if (!fs.existsSync(zipPath)) {
            console.log(`❌ File ${zipPath} tidak ditemukan, lewati...`);
            continue;
        }

        console.log(`Mengekstrak ${zipPath}...`);
        try {
            const zip = new AdmZip(zipPath);
            const zipEntries = zip.getEntries().filter(entry =>
                entry.name.toLowerCase().endsWith('.mp3')
            );
            console.log(`  Ditemukan ${zipEntries.length} file MP3`);

            for (let i = 0; i < zipEntries.length; i++) {
                const entry = zipEntries[i];
                try {
                    const mp3Buffer = entry.getData();

                    const { data, error } = await supabase.storage
                        .from('audio')
                        .upload(entry.name, mp3Buffer, {
                            contentType: 'audio/mpeg',
                            upsert: true
                        });

                    if (error) {
                        console.error(`  ❌ Gagal upload ${entry.name}:`, error.message);
                    } else {
                        if (i % 5 === 0) {
                            console.log(`  ✅ Uploaded ${i+1}/${zipEntries.length}: ${entry.name}`);
                        }
                    }
                } catch (err) {
                    console.error(`  ❌ Gagal upload ${entry.name}:`, err.message);
                }
            }
            console.log(`✅ Selesai upload audio dari ${zipPath}`);
        } catch (err) {
            console.error(`❌ Gagal ektrak ${zipPath}:`, err.message);
        }
    }
}

// === 3. LOAD DATA JSON DAN INSERT KE TABLE SOAL_EPS ===
async function loadJsonToTable() {
    console.log('\n=== MENGLOAD DATA JSON KE TABLE SOAL_EPS ===');
    const jsonDir = path.join(__dirname, '..', 'assets', 'langit-korea-extracted');

    if (!fs.existsSync(jsonDir)) {
        console.log('❌ Direktori', jsonDir, 'tidak ditemukan');
        return;
    }

    const jsonFiles = fs.readdirSync(jsonDir)
        .filter(f => f.endsWith('.json'))
        .flatMap(f => {
            const filePath = path.join(jsonDir, f);
            try {
                const content = fs.readFileSync(filePath, 'utf8');
                const data = JSON.parse(content);
                return Array.isArray(data) ? data : [];
            } catch (err) {
                console.error(`  ❌ Gagal baca ${f}:`, err.message);
                return [];
            }
        });

    console.log(`Ditemukan ${jsonFiles.length} data soal dari JSON files`);

    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < jsonFiles.length; i++) {
        const item = jsonFiles[i];

        // Sesuaikan dengan struktur tabel soal_eps
        const soalData = {
            bab: item.bab || 1,
            tipe: item.tipe || 'membaca',
            teks_soal: item.teks_soal || item.question || '',
            gambar_url: item.gambar_url || null,
            audio_url: item.audio_url || null,
            pilihan_a: item.pilihan_a || item.option_a || '',
            pilihan_b: item.pilihan_b || item.option_b || '',
            pilihan_c: item.pilihan_c || item.option_c || '',
            pilihan_d: item.pilihan_d || item.option_d || '',
            jawaban_benar: item.jawaban_benar || item.correct_answer || '',
            penjelasan: item.penjelasan || '',
            tingkat: item.tingkat || 'mudah',
            akses: item.akses || 'free'
        };

        try {
            const { data, error } = await supabase
                .from('soal_eps')
                .upsert(soalData, { onConflict: 'id' });

            if (error) {
                console.error(`  ❌ Gagal insert soal:`, error.message);
                errorCount++;
            } else {
                successCount++;
                if (i % 10 === 0) {
                    console.log(`  ✅ Inserted ${i+1}/${jsonFiles.length}`);
                }
            }
        } catch (err) {
            console.error(`  ❌ Exception:`, err.message);
            errorCount++;
        }
    }
    console.log(`✅ Selesai load JSON: ${successCount} berhasil, ${errorCount} gagal`);
}

// === FUNGSI UTAMA ===
async function main() {
    console.log('🚀 MULAI INTEGRASI ASET KE SUPABASE');
    console.log('=====================================');

    try {
        // 1. Upload gambar
        await uploadImages();

        // 2. Upload audio dari ZIP
        await uploadAudioFromZip();

        // 3. Load JSON ke table
        await loadJsonToTable();

        console.log('\n✅ INTEGRASI SELESAI!');
        console.log('Cek di Supabase Dashboard:');
        console.log('1. Storage → buckets "images" dan "audio"');
        console.log('2. Table Editor → table "soal_eps"');
    } catch (err) {
        console.error('\n❌ INTEGRASI GAGAL:', err.message);
    }
}

// Jalankan
main();
