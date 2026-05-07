// ============================================
// Langit Korea - Login Page Integration
// Untuk login.html
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Login page loaded, initializing...');

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
        // Jika sudah login, redirect ke home atau halaman tujuan
        const urlParams = new URLSearchParams(window.location.search);
        const redirect = urlParams.get('redirect') || 'home.html';
        window.location.href = decodeURIComponent(redirect);
        return;
    }

    // ==========================================
    // 2. SETUP FORM LOGIN
    // ==========================================
    const loginForm = document.getElementById('login-form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const errorEl = document.getElementById('error-message');
    const loadingEl = document.getElementById('loading');

    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const email = emailInput ? emailInput.value : '';
            const password = passwordInput ? passwordInput.value : '';

            if (!email || !password) {
                if (errorEl) {
                    errorEl.textContent = 'Email dan password wajib diisi!';
                    errorEl.style.display = 'block';
                }
                return;
            }

            // Tampilkan loading
            if (loadingEl) loadingEl.style.display = 'block';
            if (errorEl) errorEl.style.display = 'none';

            // Lakukan login
            const result = await db.login(email, password);

            // Sembunyikan loading
            if (loadingEl) loadingEl.style.display = 'none';

            if (result.success) {
                // Login berhasil, redirect
                const urlParams = new URLSearchParams(window.location.search);
                const redirect = urlParams.get('redirect') || 'home.html';
                window.location.href = decodeURIComponent(redirect);
            } else {
                // Tampilkan error
                if (errorEl) {
                    errorEl.textContent = 'Login gagal: ' + result.error;
                    errorEl.style.display = 'block';
                }
            }
        });
    }

    // ==========================================
    // 3. TOMBOL REGISTER
    // ==========================================
    const registerLink = document.getElementById('register-link');
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = 'onboarding.html';
        });
    }

    // ==========================================
    // 4. TOMBOL BACK
    // ==========================================
    const backBtn = document.getElementById('back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            window.location.href = 'index.html';
        });
    }

    console.log('Login page initialization complete!');
});
