// ============================================
// Langit Korea - Onboarding/Register Integration
// Untuk onboarding.html
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Onboarding page loaded, initializing...');

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
    if (isLoggedIn) {
        // Jika sudah login, redirect ke home
        window.location.href = 'home.html';
        return;
    }

    // ==========================================
    // 2. SETUP FORM REGISTER
    // ==========================================
    const registerForm = document.getElementById('register-form');
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const levelSelect = document.getElementById('level');
    const errorEl = document.getElementById('error-message');
    const loadingEl = document.getElementById('loading');
    const step1El = document.getElementById('step-1');
    const step2El = document.getElementById('step-2');

    // Step 1: Pilih level
    const levelButtons = document.querySelectorAll('.level-btn');
    let selectedLevel = '';

    levelButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            levelButtons.forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            selectedLevel = this.getAttribute('data-level');

            // Lanjut ke step 2
            if (step1El) step1El.style.display = 'none';
            if (step2El) step2El.style.display = 'block';
        });
    });

    // Step 2: Isi data diri
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const nama = nameInput ? nameInput.value : '';
            const email = emailInput ? emailInput.value : '';
            const password = passwordInput ? passwordInput.value : '';
            const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';

            // Validasi
            if (!selectedLevel) {
                if (errorEl) {
                    errorEl.textContent = 'Pilih level belajar dulu!';
                    errorEl.style.display = 'block';
                }
                return;
            }

            if (!nama || !email || !password) {
                if (errorEl) {
                    errorEl.textContent = 'Semua field wajib diisi!';
                    errorEl.style.display = 'block';
                }
                return;
            }

            if (password !== confirmPassword) {
                if (errorEl) {
                    errorEl.textContent = 'Password dan konfirmasi tidak cocok!';
                    errorEl.style.display = 'block';
                }
                return;
            }

            if (password.length < 6) {
                if (errorEl) {
                    errorEl.textContent = 'Password minimal 6 karakter!';
                    errorEl.style.display = 'block';
                }
                return;
            }

            // Tampilkan loading
            if (loadingEl) loadingEl.style.display = 'block';
            if (errorEl) errorEl.style.display = 'none';

            // Lakukan register
            const result = await db.register(email, password, nama);

            // Sembunyikan loading
            if (loadingEl) loadingEl.style.display = 'none';

            if (result.success) {
                // Register berhasil, update level
                try {
                    const { data: { user } } = await db.db.auth.getUser();
                    if (user) {
                        await db.db
                            .from('users')
                            .update({ level_awal: selectedLevel })
                            .eq('id', user.id);
                    }
                } catch (err) {
                    console.error('Error update level:', err);
                }

                // Redirect ke halaman tujuan
                const urlParams = new URLSearchParams(window.location.search);
                const redirect = urlParams.get('redirect') || 'home.html';
                window.location.href = decodeURIComponent(redirect);
            } else {
                // Tampilkan error
                if (errorEl) {
                    errorEl.textContent = 'Register gagal: ' + result.error;
                    errorEl.style.display = 'block';
                }
            }
        });
    }

    // ==========================================
    // 3. TOMBOL BACK
    // ==========================================
    const backBtn = document.getElementById('back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            // Cek apakah di step 2
            if (step2El && step2El.style.display === 'block') {
                // Kembali ke step 1
                step2El.style.display = 'none';
                step1El.style.display = 'block';
            } else {
                // Kembali ke halaman sebelumnya
                window.history.back();
            }
        });
    }

    // ==========================================
    // 4. TOMBOL LOGIN
    // ==========================================
    const loginLink = document.getElementById('login-link');
    if (loginLink) {
        loginLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = 'login.html';
        });
    }

    console.log('Onboarding page initialization complete!');
});
