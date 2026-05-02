# 🚀 Test Langit Korea dengan Zed.dev (Gampang Banget!)

## ✅ Kenapa Zed.dev?
- ✅ Sudah ada server HTTP built-in
- ✅ Live reload otomatis
- ✅ Tidak perlu install apa-apa lagi
- ✅ Firebase popup akan bekerja normal

---

## 📁 Langkah 1: Buka Project di Zed

### 1. Buka Zed.dev
- Buka aplikasi **Zed.dev**
- Pilih **"Open Folder"** atau **"Open Project"**
- Pilih folder: `C:\Users\jmbt\Documents\Langit Korea`

### 2. Jalankan Server
Di Zed, cari menu atau gunakan shortcut:
- **Ctrl+Shift+P** (buka command palette)
- Ketik: **"Start Server"**
- Pilih port: **8000** (atau default)
- Tekan Enter

Zed akan menampilkan:
```
Server running at http://localhost:8000
Live reload: enabled
```

---

## 📂 Langkah 2: Test di Browser

### 1. Buka Browser
Buka: **http://localhost:8000**

### 2. Otomatis Redirect
Kamu akan diarahkan ke: `http://localhost:8000/onboarding.html`

### 3. Klik "Continue with Google"
- Popup Google akan muncul
- Pilih akun Google kamu
- Izinkan akses

### 4. Berhasil!
Kamu akan diarahkan ke `home.html` dengan:
- ✅ Foto profil di header
- ✅ Nama kamu tampil
- ✅ Tombol "Logout" tersedia

---

## 📃 Langkah 3: Update Firebase Config

### 1. Buka file ini di Zed:
```
js/auth/firebase-config.js
```

### 2. Ganti dengan config asli:
```javascript
const firebaseConfig = {
    apiKey: "AIzaSyA...",           // ← Ganti!
    authDomain: "langit-korea-xxxx.firebaseapp.com",
    projectId: "langit-korea-xxxx",
    storageBucket: "langit-korea-xxxx.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abc123def456..."
};
```

**Cara dapat config:**
1. Buka https://console.firebase.google.com/
2. Pilih project "Langit Korea"
3. Klik icon gear ⚙ → "Project settings"
4. Scroll ke bawah → "Your apps" → Klik icon `</>` (Web)
5. Copy `firebaseConfig` dan paste ke file

---

## 📄 Langkah 4: Test Login

### 1. Refresh halaman
Buka: http://localhost:8000/

### 2. Klik "Continue with Google"
- Izinkan popup untuk `localhost:8000`
- Pilih akun Google

### 3. Berhasil Masuk!
Di `home.html` kamu akan lihat:
- ✅ Header: Foto + Nama kamu
- ✅ Stats: Hari Belajar, Soal Dijawab, Rata-rata Skor
- ✅ Menu: Listening, Reading, Practice, Vocabulary
- ✅ Tombol "Logout" di bawah

---

## 🔧 Troubleshooting

### ❌ "Firebase is not defined"
- Pastikan script Firebase SDK ada di HTML:
```html
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js"></script>
<script src="js/auth/firebase-config.js"></script>
```

### ❌ "Popup diblokir"
- Izinkan popup di browser untuk `localhost:8000`
- Atau matikan adblocker sementara

### ❌ "auth/operation-not-allowed"
- Pastikan Google provider **SUDAH DIAKTIFKAN** di Firebase Console
- Authentication → Sign-in method → Google → Enable

### ❌ Scores tidak muncul di home
- Cek browser console (F12) → Application → Local Storage
- Practice pages harus save ke: `listeningScore`, `readingScore`, `practiceScore`

---

## 📅 File Structure (Pastikan Sama!)

```
Langit Korea/
├── index.html              ← Entry point (redirect ke onboarding)
├── onboarding.html         ← Welcome + Auth check
├── login.html             ← Alt login page
├── home.html              ← Dashboard (perlu auth)
├── listening.html          ← Listening practice
├── reading.html           ← Reading practice
├── latihan-eps.html       ← EPS practice
├── hangul-path.html        ← Hangul learning
├── vocabulary.html         ← NEW! Flashcards
├── css/
│   └── style.css
├── js/
│   ├── auth/
│   │   └── firebase-config.js  ← UPDATE FILE INI!
│   ├── reading.js
│   └── ...
└── assets/
    ├── audio/
    └── images/
```

---

## 🎯 Status Sekarang!

| Fitur | Status | Keterangan |
|--------|--------|-------------|
| **Home** | ✅ Ready | Dashboard utama |
| **Listening** | ✅ Ready | Latihan mendengarkan |
| **Reading** | ✅ Ready | Latihan membaca + Gambar |
| **Practice** | ✅ Ready | Latihan soal EPS |
| **Hangul** | ✅ Ready | 24 pelajaran standar |
| **Vocabulary** | ✅ NEW! | Flashcards + Kategori |
| **Firebase Auth** | ⚠ Perlu config | Update `js/auth/firebase-config.js` |
| **Testing** | ✅ Siap di Zed | `http://localhost:8000` |

---

## 🚀 Lanjutkan!

1. **Buka Zed.dev** → Open folder `Langit Korea`
2. **Start Server** → `Ctrl+Shift+P` → "Start Server"
3. **Update `js/auth/firebase-config.js`** dengan config asli
4. **Test login** → Buka http://localhost:8000/
5. **Berhasil!** 🎉

Selamat mencoba! Jika ada error, cek **Console** di browser (F12) untuk detailnya! 🚀
