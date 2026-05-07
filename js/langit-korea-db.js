// ============================================
// Langit Korea - Database Operations
// File ini berisi fungsi-fungsi untuk berinteraksi
// dengan Supabase database
// ============================================

// Pastikan db (Supabase client) sudah terinisialisasi dari supabase-config.js
const LangitDB = (() => {
    // Cek apakah db sudah siap
    if (!window.db) {
        console.error("Supabase client belum siap! Pastikan supabase-config.js sudah diload.");
        return null;
    }

    const database = window.db;

    // ==========================================
    // 1. SOAL EPS-TOPIK
    // ==========================================

    /**
     * Ambil soal berdasarkan unit dan tipe
     * @param {number} unit - Nomor unit (31-60)
     * @param {string} tipe - 'membaca' atau 'mendengarkan'
     * @param {number} limit - Jumlah soal (default: 10)
     * @returns {Promise<Array>} - Array soal
     */
    async function ambilSoalEPS(unit, tipe, limit = 10) {
        try {
            let query = database
                .from('soal_eps')
                .select('*')
                .eq('unit', unit)
                .eq('tipe', tipe)
                .eq('akses', 'free') // Hanya ambil yang free dulu
                .order('id', { ascending: true });

            if (limit > 0) {
                query = query.limit(limit);
            }

            const { data, error } = await query;

            if (error) {
                console.error('Error ambil soal EPS:', error);
                return [];
            }

            return data || [];
        } catch (err) {
            console.error('Exception ambil soal EPS:', err);
            return [];
        }
    }

    /**
     * Ambil soal untuk simulasi (campur membaca & mendengarkan)
     * @param {number} jumlahMembaca - Jumlah soal membaca (default: 20)
     * @param {number} jumlahMendengar - Jumlah soal mendengar (default: 20)
     * @returns {Promise<Array>} - Array soal tercampur
     */
    async function ambilSoalSimulasi(jumlahMembaca = 20, jumlahMendengar = 20) {
        try {
            // Ambil soal membaca
            const { data: dataMembaca, error: errMembaca } = await database
                .from('soal_eps')
                .select('*')
                .eq('tipe', 'membaca')
                .eq('akses', 'free')
                .order('unit', { ascending: true })
                .limit(jumlahMembaca);

            if (errMembaca) {
                console.error('Error ambil soal membaca:', errMembaca);
            }

            // Ambil soal mendengarkan
            const { data: dataMendengar, error: errMendengar } = await database
                .from('soal_eps')
                .select('*')
                .eq('tipe', 'mendengarkan')
                .eq('akses', 'free')
                .order('unit', { ascending: true })
                .limit(jumlahMendengar);

            if (errMendengar) {
                console.error('Error ambil soal mendengar:', errMendengar);
            }

            // Gabungkan dan acak urutannya
            const semuaSoal = [
                ...(dataMembaca || []),
                ...(dataMendengar || [])
            ];

            // Acak array (Fisher-Yates shuffle)
            for (let i = semuaSoal.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [semuaSoal[i], semuaSoal[j]] = [semuaSoal[j], semuaSoal[i]];
            }

            return semuaSoal;
        } catch (err) {
            console.error('Exception ambil soal simulasi:', err);
            return [];
        }
    }

    // ==========================================
    // 2. SOAL HANGUL
    // ==========================================

    /**
     * Ambil semua soal Hangul
     * @returns {Promise<Array>} - Array soal Hangul
     */
    async function ambilSoalHangul() {
        try {
            const { data, error } = await database
                .from('soal_hangul')
                .select('*')
                .order('urutan', { ascending: true });

            if (error) {
                console.error('Error ambil soal Hangul:', error);
                return [];
            }

            return data || [];
        } catch (err) {
            console.error('Exception ambil soal Hangul:', err);
            return [];
        }
    }

    // ==========================================
    // 3. USER & AUTH
    // ==========================================

    /**
     * Register user baru
     * @param {string} email
     * @param {string} password
     * @param {string} nama
     * @returns {Promise<Object>} - { success, user, error }
     */
    async function register(email, password, nama) {
        try {
            // Daftar di Supabase Auth
            const { data: authData, error: authError } = await database.auth.signUp({
                email: email,
                password: password
            });

            if (authError) {
                return { success: false, error: authError.message };
            }

            // Insert ke tabel users
            if (authData.user) {
                const { error: dbError } = await database
                    .from('users')
                    .insert([
                        {
                            id: authData.user.id,
                            email: email,
                            nama: nama,
                            level_awal: 'pemula',
                            status: 'free'
                        }
                    ]);

                if (dbError) {
                    console.error('Error insert user:', dbError);
                }
            }

            return { success: true, user: authData.user };
        } catch (err) {
            console.error('Exception register:', err);
            return { success: false, error: err.message };
        }
    }

    /**
     * Login user
     * @param {string} email
     * @param {string} password
     * @returns {Promise<Object>} - { success, user, error }
     */
    async function login(email, password) {
        try {
            const { data, error } = await database.auth.signInWithPassword({
                email: email,
                password: password
            });

            if (error) {
                return { success: false, error: error.message };
            }

            return { success: true, user: data.user };
        } catch (err) {
            console.error('Exception login:', err);
            return { success: false, error: err.message };
        }
    }

    /**
     * Logout user
     */
    async function logout() {
        try {
            await database.auth.signOut();
            return { success: true };
        } catch (err) {
            console.error('Exception logout:', err);
            return { success: false, error: err.message };
        }
    }

    /**
     * Ambil profil user yang sedang login
     * @returns {Promise<Object|null>} - Data user atau null
     */
    async function ambilProfilUser() {
        try {
            const { data: { user } } = await database.auth.getUser();

            if (!user) return null;

            const { data, error } = await database
                .from('users')
                .select('*')
                .eq('id', user.id)
                .single();

            if (error) {
                console.error('Error ambil profil:', error);
                return null;
            }

            return data;
        } catch (err) {
            console.error('Exception ambil profil:', err);
            return null;
        }
    }

    // ==========================================
    // 4. PROGRESS USER
    // ==========================================

    /**
     * Simpan progress user (setelah menjawab soal)
     * @param {number} soalId - ID soal
     * @param {string} tipeSoal - 'hangul' atau 'eps'
     * @param {string} jawabanUser - Jawaban user (a/b/c/d)
     * @param {boolean} benar - Apakah jawaban benar
     * @returns {Promise<boolean>} - Success/failure
     */
    async function simpanProgress(soalId, tipeSoal, jawabanUser, benar) {
        try {
            const { data: { user } } = await database.auth.getUser();

            if (!user) {
                console.warn('User belum login, progress tidak disimpan');
                return false;
            }

            const { error } = await database
                .from('progress_user')
                .insert([
                    {
                        user_id: user.id,
                        soal_id: soalId,
                        tipe_soal: tipeSoal,
                        jawaban_user: jawabanUser,
                        benar: benar
                    }
                ]);

            if (error) {
                console.error('Error simpan progress:', error);
                return false;
            }

            return true;
        } catch (err) {
            console.error('Exception simpan progress:', err);
            return false;
        }
    }

    /**
     * Ambil statistik progress user
     * @returns {Promise<Object>} - Statistik belajar
     */
    async function ambilStatistikUser() {
        try {
            const { data: { user } } = await database.auth.getUser();

            if (!user) return null;

            // Ambil total soal yang dikerjakan
            const { count: totalDikerjakan, error: err1 } = await database
                .from('progress_user')
                .select('*', { count: 'exact', head: true })
                .eq('user_id', user.id);

            // Ambil jumlah benar
            const { count: totalBenar, error: err2 } = await database
                .from('progress_user')
                .select('*', { count: 'exact', head: true })
                .eq('user_id', user.id)
                .eq('benar', true);

            // Ambil streak (belum diimplementasi, placeholder)
            const streak = 0;

            return {
                totalDikerjakan: totalDikerjakan || 0,
                totalBenar: totalBenar || 0,
                streak: streak,
                persentase: totalDikerjakan > 0
                    ? Math.round((totalBenar / totalDikerjakan) * 100)
                    : 0
            };
        } catch (err) {
            console.error('Exception ambil statistik:', err);
            return null;
        }
    }

    // ==========================================
    // 5. SIMULASI HASIL
    // ==========================================

    /**
     * Simpan hasil simulasi
     * @param {number} skorMembaca
     * @param {number} skorMendengar
     * @param {number} totalSoal
     * @param {number} durasiDetik
     * @returns {Promise<boolean>} - Success/failure
     */
    async function simpanHasilSimulasi(skorMembaca, skorMendengar, totalSoal, durasiDetik) {
        try {
            const { data: { user } } = await database.auth.getUser();

            if (!user) {
                console.warn('User belum login, hasil tidak disimpan');
                return false;
            }

            const skorTotal = skorMembaca + skorMendengar;

            const { error } = await database
                .from('simulasi_hasil')
                .insert([
                    {
                        user_id: user.id,
                        skor_membaca: skorMembaca,
                        skor_mendengar: skorMendengar,
                        skor_total: skorTotal,
                        total_soal: totalSoal,
                        durasi_detik: durasiDetik
                    }
                ]);

            if (error) {
                console.error('Error simpan hasil simulasi:', error);
                return false;
            }

            return true;
        } catch (err) {
            console.error('Exception simpan hasil simulasi:', err);
            return false;
        }
    }

    // ==========================================
    // 6. UTILITY
    // ==========================================

    /**
     * Cek apakah user sudah login
     * @returns {Promise<boolean>}
     */
    async function cekUserLogin() {
        try {
            const { data: { user } } = await database.auth.getUser();
            return !!user;
        } catch {
            return false;
        }
    }

    /**
     * Listen to auth state changes
     * @param {Function} callback - Callback function (event, session)
     */
    function onAuthStateChange(callback) {
        return database.auth.onAuthStateChange(callback);
    }

    // Return semua fungsi publik
    return {
        // Soal
        ambilSoalEPS,
        ambilSoalSimulasi,
        ambilSoalHangul,

        // Auth
        register,
        login,
        logout,
        ambilProfilUser,
        cekUserLogin,
        onAuthStateChange,

        // Progress
        simpanProgress,
        ambilStatistikUser,

        // Simulasi
        simpanHasilSimulasi,

        // Database instance (for advanced use)
        db: database
    };
})();

// Export ke global scope
window.LangitDB = LangitDB;
