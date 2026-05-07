// ============================================
// Langit Korea - Simulasi Page Integration
// Untuk simulasi.html
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Simulasi page loaded, initializing...');

    // Cek apakah LangitDB sudah siap
    if (!window.LangitDB) {
        console.error('LangitDB belum siap! Pastikan langit-korea-db.js sudah diload.');
        return;
    }

    const db = window.LangitDB;

    // ==========================================
    // 1. CEK STATUS LOGIN
    // ==========================================
    const isLoggedIn = await db.cekUserLogin();
    if (!isLoggedIn) {
        const shouldRedirect = confirm('Kamu belum login. Login untuk menyimpan hasil simulasi?');
        if (shouldRedirect) {
            window.location.href = 'login.html?redirect=' + encodeURIComponent(window.location.href);
            return;
        }
    }

    // ==========================================
    // 2. AMBIL SOAL SIMULASI
    // ==========================================
    const loadingEl = document.getElementById('loading');
    const simulasiContainer = document.getElementById('simulasi-container');

    if (loadingEl) loadingEl.style.display = 'block';
    if (simulasiContainer) simulasiContainer.style.display = 'none';

    // Ambil 40 soal (20 membaca + 20 mendengar)
    const soalList = await db.ambilSoalSimulasi(20, 20);

    if (loadingEl) loadingEl.style.display = 'none';

    if (!soalList || soalList.length === 0) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = 'Soal simulasi belum tersedia.';
            errorEl.style.display = 'block';
        }
        return;
    }

    if (simulasiContainer) simulasiContainer.style.display = 'block';

    // ==========================================
    // 3. INISIALISASI SIMULASI
    // ==========================================
    let currentSoalIndex = 0;
    let jawabanUser = {};
    let benarMembaca = 0;
    let benarMendengar = 0;
    let startTime = Date.now();
    let timerInterval;
    const totalSoal = soalList.length;
    const durasiMenit = 50; // 50 menit sesuai aturan EPS-TOPIK
    let waktuTersisa = durasiMenit * 60; // dalam detik

    // Mulai timer
    function mulaiTimer() {
        timerInterval = setInterval(() => {
            waktuTersisa--;

            const timerEl = document.getElementById('timer');
            if (timerEl) {
                const menit = Math.floor(waktuTersisa / 60);
                const detik = waktuTersisa % 60;
                timerEl.textContent = `${menit.toString().padStart(2, '0')}:${detik.toString().padStart(2, '0')}`;
            }

            // Peringatan waktu
            if (waktuTersisa <= 300) { // 5 menit terakhir
                const timerEl = document.getElementById('timer');
                if (timerEl) timerEl.classList.add('warning');
            }

            // Waktu habis
            if (waktuTersisa <= 0) {
                clearInterval(timerInterval);
                selesaiSimulasi();
            }
        }, 1000);
    }

    mulaiTimer();

    // ==========================================
    // 4. TAMPILKAN SOAL
    // ==========================================
    function tampilkanSoal(index) {
        if (index < 0 || index >= soalList.length) return;

        const soal = soalList[index];
        const soalEl = document.getElementById('soal-content');
        const progressEl = document.getElementById('progress');
        const counterEl = document.getElementById('soal-counter');
        const tipeEl = document.getElementById('soal-tipe');

        if (!soalEl) return;

        // Update progress
        if (progressEl) {
            const progress = ((index + 1) / totalSoal) * 100;
            progressEl.style.width = progress + '%';
        }

        if (counterEl) {
            counterEl.textContent = `Soal ${index + 1} dari ${totalSoal}`;
        }

        if (tipeEl) {
            tipeEl.textContent = soal.tipe === 'membaca' ? 'Membaca' : 'Mendengarkan';
            tipeEl.className = soal.tipe === 'membaca' ? 'tipe-membaca' : 'tipe-mendengar';
        }

        // Tampilkan teks soal
        let html = `
            <div class="soal-item" data-id="${soal.id}" data-tipe="${soal.tipe}">
                <p class="soal-teks">${soal.teks_soal}</p>
        `;

        // Jika ada gambar soal
        if (soal.gambar_url) {
            html += `<img src="${soal.gambar_url}" alt="Gambar soal" class="soal-gambar">`;
        }

        // Pilihan jawaban
        html += `<div class="pilihan-container">`;

        const pilihan = [
            { key: 'a', teks: soal.pilihan_a, gambar: soal.pilihan_a_gambar_url },
            { key: 'b', teks: soal.pilihan_b, gambar: soal.pilihan_b_gambar_url },
            { key: 'c', teks: soal.pilihan_c, gambar: soal.pilihan_c_gambar_url },
            { key: 'd', teks: soal.pilihan_d, gambar: soal.pilihan_d_gambar_url }
        ];

        pilihan.forEach(p => {
            const selectedClass = jawabanUser[soal.id] === p.key ? 'selected' : '';
            html += `
                <div class="pilihan-item ${selectedClass}" data-jawaban="${p.key}">
                    ${p.gambar ? `<img src="${p.gambar}" alt="Gambar pilihan" class="pilihan-gambar">` : ''}
                    <span class="pilihan-teks">${p.teks}</span>
                    <span class="pilihan-label">${p.key.toUpperCase()}</span>
                </div>
            `;
        });

        html += `</div>`; // Tutup pilihan-container

        // Audio player untuk mendengarkan
        if (soal.tipe === 'mendengarkan' && soal.audio_url) {
            html += `
                <div class="audio-player">
                    <audio controls>
                        <source src="${soal.audio_url}" type="audio/mpeg">
                        Browser kamu tidak mendukung audio player.
                    </audio>
                </div>
            `;
        }

        html += `</div>`; // Tutup soal-item

        soalEl.innerHTML = html;

        // Tambahkan event listener ke pilihan
        const pilihanItems = soalEl.querySelectorAll('.pilihan-item');
        pilihanItems.forEach(item => {
            item.addEventListener('click', function() {
                // Hapus selected sebelumnya
                pilihanItems.forEach(i => i.classList.remove('selected'));
                // Tambah selected ke yang diklik
                this.classList.add('selected');

                // Simpan jawaban
                const jawaban = this.getAttribute('data-jawaban');
                jawabanUser[soal.id] = {
                    jawaban: jawaban,
                    tipe: soal.tipe,
                    benar: jawaban === soal.jawaban
                };

                // Update counter benar
                if (jawaban === soal.jawaban) {
                    if (soal.tipe === 'membaca') benarMembaca++;
                    else benarMendengar++;
                }
            });
        });
    }

    // ==========================================
    // 5. NAVIGASI SOAL
    // ==========================================
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    const finishBtn = document.getElementById('finish-btn');

    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (currentSoalIndex < soalList.length - 1) {
                currentSoalIndex++;
                tampilkanSoal(currentSoalIndex);

                // Sembunyikan tombol prev jika di soal pertama
                if (currentSoalIndex === 0 && prevBtn) {
                    prevBtn.style.display = 'none';
                } else if (prevBtn) {
                    prevBtn.style.display = 'block';
                }

                // Tampilkan tombol finish jika di soal terakhir
                if (currentSoalIndex === soalList.length - 1 && finishBtn) {
                    finishBtn.style.display = 'block';
                    nextBtn.style.display = 'none';
                }
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (currentSoalIndex > 0) {
                currentSoalIndex--;
                tampilkanSoal(currentSoalIndex);

                // Sembunyikan tombol prev jika di soal pertama
                if (currentSoalIndex === 0) {
                    prevBtn.style.display = 'none';
                }

                // Tampilkan tombol next, sembunyikan finish
                if (nextBtn) nextBtn.style.display = 'block';
                if (finishBtn) finishBtn.style.display = 'none';
            }
        });
    }

    if (finishBtn) {
        finishBtn.addEventListener('click', function() {
            // Konfirmasi sebelum selesai
            const confirmFinish = confirm('Yakin ingin menyelesaikan simulasi?');
            if (confirmFinish) {
                selesaiSimulasi();
            }
        });
    }

    // ==========================================
    // 6. SELESAIKAN SIMULASI
    // ==========================================
    async function selesaiSimulasi() {
        clearInterval(timerInterval);

        const durasiDetik = Math.floor((Date.now() - startTime) / 1000);
        const skorMembaca = benarMembaca;
        const skorMendengar = benarMendengar;
        const skorTotal = skorMembaca + skorMendengar;

        // Simpan hasil ke database jika login
        if (isLoggedIn) {
            await db.simpanHasilSimulasi(skorMembaca, skorMendengar, totalSoal, durasiDetik);

            // Simpan juga progress per soal
            for (const [soalId, data] of Object.entries(jawabanUser)) {
                await db.simpanProgress(
                    parseInt(soalId),
                    data.tipe,
                    data.jawaban,
                    data.benar
                );
            }
        }

        // Redirect ke halaman hasil
        window.location.href = `hasil-simulasi.html?skorMembaca=${skorMembaca}&skorMendengar=${skorMendengar}&total=${totalSoal}&durasi=${durasiDetik}`;
    }

    // ==========================================
    // 7. TAMPILKAN SOAL PERTAMA
    // ==========================================
    tampilkanSoal(currentSoalIndex);

    // Sembunyikan tombol prev di soal pertama
    if (prevBtn && currentSoalIndex === 0) {
        prevBtn.style.display = 'none';
    }

    console.log('Simulasi page initialization complete!');
});
