// ============================================
// Langit Korea - Home Page Integration
// Mengintegrasikan Supabase dengan home.html
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Home page loaded, initializing...');

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
    const authSection = document.getElementById('auth-section');
    const userSection = document.getElementById('user-section');
    const userNameEl = document.getElementById('user-name');
    const userStatusEl = document.getElementById('user-status');

    if (isLoggedIn) {
        // Ambil profil user
        const profil = await db.ambilProfilUser();

        if (profil) {
            // Tampilkan section user
            if (authSection) authSection.style.display = 'none';
            if (userSection) userSection.style.display = 'block';
            if (userNameEl) userNameEl.textContent = profil.nama || 'User';
            if (userStatusEl) {
                userStatusEl.textContent = profil.status === 'premium' ? 'Premium 🌟' : 'Free';
                userStatusEl.className = profil.status === 'premium' ? 'status-premium' : 'status-free';
            }

            // Ambil statistik
            const statistik = await db.ambilStatistikUser();
            if (statistik) {
                const elTotalSoal = document.getElementById('total-soal');
                const elBenar = document.getElementById('total-benar');
                const elPersen = document.getElementById('persentase');
                const elStreak = document.getElementById('streak');

                if (elTotalSoal) elTotalSoal.textContent = statistik.totalDikerjakan;
                if (elBenar) elBenar.textContent = statistik.totalBenar;
                if (elPersen) elPersen.textContent = statistik.persentase + '%';
                if (elStreak) elStreak.textContent = statistik.streak;
            }
        }
    } else {
        // Tampilkan section auth
        if (authSection) authSection.style.display = 'block';
        if (userSection) userSection.style.display = 'none';
    }

    // ==========================================
    // 2. SETUP EVENT LISTENERS
    // ==========================================

    // Tombol Login
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            window.location.href = 'login.html';
        });
    }

    // Tombol Register
    const registerBtn = document.getElementById('register-btn');
    if (registerBtn) {
        registerBtn.addEventListener('click', function() {
            window.location.href = 'onboarding.html';
        });
    }

    // Tombol Logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            const result = await db.logout();
            if (result.success) {
                window.location.reload();
            } else {
                alert('Gagal logout: ' + result.error);
            }
        });
    }

    // ==========================================
    // 3. TARGET HARIAN (DINAMIS)
    // ==========================================
    const targetList = document.getElementById('target-list');
    if (targetList && isLoggedIn) {
        // Ambil 3 unit berikutnya yang belum diselesaikan
        // Ini contoh sederhana, bisa dikembangkan lagi
        const targetItems = [
            { unit: 31, judul: 'Pakaian dan Sikap Kerja', progress: 0 },
            { unit: 32, judul: 'Penggunaan Fasilitas Perusahaan', progress: 0 },
            { unit: 33, judul: 'Hubungan dengan Rekan Kerja', progress: 0 }
        ];

        targetList.innerHTML = '';
        targetItems.forEach(item => {
            const li = document.createElement('li');
            li.className = 'target-item';
            li.innerHTML = `
                <div class="target-info">
                    <h4>Unit ${item.unit}: ${item.judul}</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${item.progress}%"></div>
                    </div>
                    <span class="progress-text">${item.progress}% selesai</span>
                </div>
                <a href="latihan-eps.html?unit=${item.unit}" class="btn-latihan">Latihan</a>
            `;
            targetList.appendChild(li);
        });
    }

    // ==========================================
    // 4. QUICK STATS (JIKA ADA)
    // ==========================================
    const quickStats = document.getElementById('quick-stats');
    if (quickStats && isLoggedIn) {
        const statistik = await db.ambilStatistikUser();
        if (statistik) {
            quickStats.innerHTML = `
                <div class="stat-card">
                    <i class="fas fa-check-circle"></i>
                    <h3>${statistik.totalBenar}</h3>
                    <p>Jawaban Benar</p>
                </div>
                <div class="stat-card">
                    <i class="fas fa-question-circle"></i>
                    <h3>${statistik.totalDikerjakan}</h3>
                    <p>Soal Dikerjakan</p>
                </div>
                <div class="stat-card">
                    <i class="fas fa-chart-line"></i>
                    <h3>${statistik.persentase}%</h3>
                    <p>Persentase</p>
                </div>
            `;
        }
    }

    // ==========================================
    // 5. LISTENER UNTUK AUTH STATE CHANGE
    // ==========================================
    db.onAuthStateChange((event, session) => {
        console.log('Auth state changed:', event);
        if (event === 'SIGNED_IN') {
            window.location.reload();
        } else if (event === 'SIGNED_OUT') {
            window.location.reload();
        }
    });

    console.log('Home page initialization complete!');
});

// Fungsi untuk navigasi ke halaman latihan
function bukaLatihan(tipe) {
    if (tipe === 'membaca') {
        window.location.href = 'latihan-eps.html?tipe=membaca';
    } else if (tipe === 'mendengarkan') {
        window.location.href = 'listening.html';
    } else if (tipe === 'simulasi') {
        window.location.href = 'simulasi.html';
    } else if (tipe === 'hangul') {
        window.location.href = 'hangul-path.html';
    }
}

// Export fungsi ke global scope
window.bukaLatihan = bukaLatihan;
