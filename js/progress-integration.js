// ============================================
// Langit Korea - Progress Page Integration
// Untuk progress.html
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Progress page loaded, initializing...');

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
        window.location.href = 'login.html?redirect=' + encodeURIComponent(window.location.href);
        return;
    }

    // ==========================================
    // 2. AMBIL PROFIL & STATISTIK
    // ==========================================
    const profil = await db.ambilProfilUser();
    const statistik = await db.ambilStatistikUser();

    // Tampilkan profil
    const userNameEl = document.getElementById('user-name');
    const userStatusEl = document.getElementById('user-status');

    if (profil) {
        if (userNameEl) userNameEl.textContent = profil.nama || 'User';
        if (userStatusEl) {
            userStatusEl.textContent = profil.status === 'premium' ? 'Premium 🌟' : 'Free';
            userStatusEl.className = profil.status === 'premium' ? 'status-premium' : 'status-free';
        }
    }

    // Tampilkan statistik
    if (statistik) {
        const elTotalDikerjakan = document.getElementById('total-dikerjakan');
        const elTotalBenar = document.getElementById('total-benar');
        const elPersentase = document.getElementById('persentase');
        const elStreak = document.getElementById('streak');

        if (elTotalDikerjakan) elTotalDikerjakan.textContent = statistik.totalDikerjakan;
        if (elTotalBenar) elTotalBenar.textContent = statistik.totalBenar;
        if (elPersentase) elPersentase.textContent = statistik.persentase + '%';
        if (elStreak) elStreak.textContent = statistik.streak;

        // Update progress bar
        const progressBar = document.getElementById('overall-progress');
        if (progressBar) {
            progressBar.style.width = statistik.persentase + '%';
        }
    }

    // ==========================================
    // 3. AMBIL RIWAYAT SIMULASI
    // ==========================================
    const riwayatEl = document.getElementById('riwayat-simulasi');

    try {
        const { data: { user } } = await db.db.auth.getUser();

        if (user) {
            const { data, error } = await db.db
                .from('simulasi_hasil')
                .select('*')
                .eq('user_id', user.id)
                .order('selesai_at', { ascending: false })
                .limit(10);

            if (error) {
                console.error('Error ambil riwayat:', error);
            } else if (data && data.length > 0) {
                if (riwayatEl) {
                    let html = '<ul class="riwayat-list">';

                    data.forEach(item => {
                        const tanggal = new Date(item.selesai_at).toLocaleDateString('id-ID');
                        const menit = Math.floor(item.durasi_detik / 60);
                        const detik = item.durasi_detik % 60;

                        html += `
                            <li class="riwayat-item">
                                <div class="riwayat-tanggal">${tanggal}</div>
                                <div class="riwayat-skor">
                                    <span class="skor-membaca">Membaca: ${item.skor_membaca}</span>
                                    <span class="skor-mendengar">Mendengar: ${item.skor_mendengar}</span>
                                    <span class="skor-total">Total: ${item.skor_total}</span>
                                </div>
                                <div class="riwayat-durasi">${menit}m ${detik}d</div>
                            </li>
                        `;
                    });

                    html += '</ul>';
                    riwayatEl.innerHTML = html;
                }
            } else {
                if (riwayatEl) {
                    riwayatEl.innerHTML = '<p class="empty-state">Belum ada riwayat simulasi. Yuk, mulai latihan!</p>';
                }
            }
        }
    } catch (err) {
        console.error('Exception ambil riwayat:', err);
    }

    // ==========================================
    // 4. AMBIL PROGRESS PER UNIT
    // ==========================================
    const progressUnitEl = document.getElementById('progress-per-unit');

    try {
        const { data: { user } } = await db.db.auth.getUser();

        if (user) {
            // Ambil semua progress user
            const { data: progressData, error } = await db.db
                .from('progress_user')
                .select(`
                    soal_id,
                    benar,
                    soal:soal_eps(unit, tipe)
                `)
                .eq('user_id', user.id);

            if (error) {
                console.error('Error ambil progress per unit:', error);
            } else if (progressData && progressData.length > 0) {
                // Hitung per unit
                const unitStats = {};

                progressData.forEach(item => {
                    if (item.soal && item.soal.unit) {
                        const unit = item.soal.unit;
                        if (!unitStats[unit]) {
                            unitStats[unit] = { total: 0, benar: 0 };
                        }
                        unitStats[unit].total++;
                        if (item.benar) unitStats[unit].benar++;
                    }
                });

                if (progressUnitEl) {
                    let html = '<div class="unit-grid">';

                    // Sort unit
                    const sortedUnits = Object.keys(unitStats).sort((a, b) => a - b);

                    sortedUnits.forEach(unit => {
                        const stats = unitStats[unit];
                        const persen = Math.round((stats.benar / stats.total) * 100);

                        html += `
                            <div class="unit-card">
                                <h4>Unit ${unit}</h4>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${persen}%"></div>
                                </div>
                                <p>${stats.benar}/${stats.total} (${persen}%)</p>
                            </div>
                        `;
                    });

                    html += '</div>';
                    progressUnitEl.innerHTML = html;
                }
            } else {
                if (progressUnitEl) {
                    progressUnitEl.innerHTML = '<p class="empty-state">Belum ada progress. Mulai latihan sekarang!</p>';
                }
            }
        }
    } catch (err) {
        console.error('Exception ambil progress per unit:', err);
    }

    // ==========================================
    // 5. TOMBOL AKSI
    // ==========================================
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            const result = await db.logout();
            if (result.success) {
                window.location.href = 'home.html';
            } else {
                alert('Gagal logout: ' + result.error);
            }
        });
    }

    const latihanBtn = document.getElementById('mulai-latihan-btn');
    if (latihanBtn) {
        latihanBtn.addEventListener('click', function() {
            window.location.href = 'latihan-eps.html';
        });
    }

    const simulasiBtn = document.getElementById('mulai-simulasi-btn');
    if (simulasiBtn) {
        simulasiBtn.addEventListener('click', function() {
            window.location.href = 'simulasi.html';
        });
    }

    console.log('Progress page initialization complete!');
});
