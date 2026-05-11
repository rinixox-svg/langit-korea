import { supabase } from './supabase.js';

export async function handleRegister(event) {
    event.preventDefault();
    const nama = document.getElementById('regNama')?.value.trim();
    const email = document.getElementById('regEmail')?.value.trim();
    const password = document.getElementById('regPassword')?.value;
    const sekolah = document.getElementById('regSekolah')?.value.trim();
    const tujuan = document.getElementById('regTujuan')?.value.trim();
    const level = document.getElementById('regLevel')?.value || 'pemula';
    const btn = document.getElementById('registerBtn');

    if (!nama || !email || !password) {
        return { success: false, error: 'Silakan lengkapi semua field' };
    }
    if (password.length < 6) {
        return { success: false, error: 'Kata sandi minimal 6 karakter' };
    }

    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Mendaftarkan...';
    }

    try {
        const { data, error } = await supabase.auth.signUp({
            email: email,
            password: password,
            options: {
                data: {
                    nama: nama,
                    sekolah: sekolah,
                    tujuan: tujuan,
                    level: level
                }
            }
        });

        if (error) throw error;

        if (data.user) {
            const { error: profileError } = await supabase
                .from('profiles')
                .insert([{
                    id: data.user.id,
                    nama: nama,
                    email: email,
                    sekolah: sekolah,
                    tujuan: tujuan,
                    level: level
                }]);

            if (profileError) {
                console.warn('Profile insert warning:', profileError);
            }
        }

        return { success: true, user: data.user, message: 'Akun berhasil dibuat!' };
    } catch (error) {
        return { success: false, error: error.message };
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Buat Akun';
        }
    }
}

export async function handleLogin(event) {
    if (event) event.preventDefault();
    const email = document.getElementById('loginEmail')?.value.trim();
    const password = document.getElementById('loginPassword')?.value;
    const btn = document.getElementById('loginBtn');

    if (!email || !password) {
        return { success: false, error: 'Silakan isi email dan kata sandi' };
    }

    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Memuat...';
    }

    try {
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password
        });

        if (error) throw error;
        return { success: true, user: data.user, session: data.session };
    } catch (error) {
        return { success: false, error: error.message };
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Masuk';
        }
    }
}

export async function handleLogout() {
    try {
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

export async function checkAuthState() {
    const { data: { user } } = await supabase.auth.getUser();
    const currentPage = window.location.pathname.split('/').pop();

    if (!user) {
        if (currentPage !== 'index.html' && currentPage !== 'onboarding.html') {
            window.location.href = 'onboarding.html';
        }
        return null;
    }

    if (currentPage === 'onboarding.html') {
        window.location.href = 'dashboard.html';
        return user;
    }

    return user;
}

export async function register(email, password, nama) {
    try {
        const { data, error } = await supabase.auth.signUp({
            email: email,
            password: password,
            options: {
                data: {
                    nama: nama
                }
            }
        });

        if (error) throw error;
        return { success: true, user: data.user, message: 'Silakan cek email untuk verifikasi.' };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

export async function login(email, password) {
    try {
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password
        });

        if (error) throw error;
        return { success: true, user: data.user, session: data.session };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

export async function logout() {
    try {
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

export function getCurrentUser() {
    return supabase.auth.getUser();
}

export function onAuthChange(callback) {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
        callback(event, session);
    });
    return subscription;
}
