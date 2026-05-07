// ============================================
// Langit Korea - Hasil Simulasi Integration
// Untuk hasil-simulasi.html
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Hasil Simulasi page loaded, initializing...');

    // Cek apakah LangitDB sudah siap
    if (!window.LangitDB) {
        console.error('LangitDB belum siap! Pastikan langit-korea-db.js sudah diload.');
        return;
    }

    const db = window.LangitDB;

    // ==========================================
    // 1. AMBIL PARAMETER URL
    // ==========================================
    const urlParams = new URLSearchParams(window.location.search);
    const skorMembaca = parseInt(urlParams.get('skorMembaca')) || 0;
    const skorMendengar = parseInt(urlParams.get('skorMendengar')) || 0;
    const totalSoal = parseInt(urlParams.get('total')) || 40;
    const durasiDetik = parseInt(urlParams.get('durasi')) || 0;
    const skorTotal = skorMembaca + skorMendengar;
    const persentase = Math.round((skorTotal / totalSoal) * 100);

    // ==========================================
    // 2. TAMPILKAN HASIL
    // ==========================================
    const skorTotalEl = document.getElementById('skor-total');
    const skorMembacaEl = document.getElementById('skor-membaca');
    const skorMendengarEl = document.getElementById('skor-mendengar');
    const persentaseEl = document.getElementById('persentase');
    const durasiEl = document.getElementById('durasi');
    const statusEl = document.getElementById('status');
    const rekomendasiEl = document.getElementById('rekomendasi');

    if (skorTotalEl) skorTotalEl.textContent = skorTotal;
    if (skorMembacaEl) skorMembacaEl.textContent = skorMembaca;
    if (skorMendengarEl) skorMendengarEl.textContent = skorMendengar;
    if (persentaseEl) persentaseEl.textContent = persentase + '%';

    // Format durasi
    if (durasiEl) {
        const menit = Math.floor(durasiDetik / 60);
        const detik = durasiDetik % 60;
        durasiEl.textContent = `${menit} menit ${detik} detik`;
    }

    // Status kelulusan (contoh: lulus jika > 60%)
    const lulus = persentase >= 60;
    if (statusEl) {
        statusEl.textContent = lulus ? 'LULUS 🎉' : 'BELUM LULUS 😊';
        statusEl.className = lulus ? 'status-lulus' : 'status-belum';
    }

    // Rekomendasi
    if (rekomendasiEl) {
        let rekomendasi = '';

        if (skorMembaca < skorMendengar) {
            rekomendasi += '<p>📖 <strong>Membaca:</strong> Fokus latihan soal membaca lebih banyak. Coba unit 31-40.</p>';
        } else {
            rekomendasi += '<p>📖 <strong>Membaca:</strong> Bagus! Pertahankan dan tingkatkan terus.</p>';
        }

        if (skorMendengar < skorMembaca) {
            rekomendasi += '<p>🎧 <strong>Mendengarkan:</strong> Latihan dengarkan audio lebih sering. Gunakan fitur listening.</p>';
        } else {
            rekomendasi += '<p>🎧 <strong>Mendengarkan:</strong> Bagus! Dengarkan berbagai aksen Korea.</p>';
        }

        if (persentase < 60) {
            rekomendasi += '<p>💪 <strong>Tips:</strong> Jangan menyerah! Latihan 15 menit setiap hari.</p>';
        } else {
            rekomendasi += '<p>🌟 <strong>Tips:</strong> Pertahankan! Kamu sudah di jalur yang benar.</p>';
        }

        rekomendasiEl.innerHTML = rekomendasi;
    }

    // ==========================================
    // 3. UPDATE PROGRESS DI DATABASE
    // ==========================================
    const isLoggedIn = await db.cekUserLogin();
    if (isLoggedIn) {
        // Simpan hasil simulasi (sudah disimpan di simulasi.js, tapi bisa diupdate di sini jika perlu)
        console.log('Hasil simulasi sudah disimpan untuk user login');
    }

    // ==========================================
    // 4. TOMBOL AKSI
    // ==========================================
    const ulangiBtn = document.getElementById('ulangi-btn');
    const homeBtn = document.getElementById('home-btn');
    const latihanBtn = document.getElementById('latihan-btn');

    if (ulangiBtn) {
        ulangiBtn.addEventListener('click', function() {
            window.location.href = 'simulasi.html';
        });
    }

    if (homeBtn) {
        homeBtn.addEventListener('click', function() {
            window.location.href = 'home.html';
        });
    }

    if (latihanBtn) {
        latihanBtn.addEventListener('click', function() {
            // Arahkan ke unit yang lemah
            if (skorMembaca < skorMendengar) {
                window.location.href = 'latihan-eps.html?unit=31&tipe=membaca';
            } else {
                window.location.href = 'listening.html?unit=31';
            }
        });
    }

    // ==========================================
    // 5. BAGIKAN HASIL (SOSMED)
    // ==========================================
    const shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', function() {
            const text = `Aku baru saja simulasi EPS-TOPIK di Langit Korea! Skor: ${skorTotal}/${totalSoal} (${persentase}%). Yuk belajar bareng! 🇰🇷`;

            if (navigator.share) {
                navigator.share({
                    title: 'Hasil Simulasi Langit Korea',
                    text: text,
                    url: window.location.origin
                });
            } else {
                // Fallback: copy ke clipboard
                navigator.clipboard.writeText(text).then(() => {
                    alert('Hasil disalin ke clipboard! Bagikan ke teman-temanmu.');
                });
            }
        });
    }

    console.log('Hasil Simulasi page initialization complete!');
});
