🎯 PENYESUAIAN PRIORITAS:

1.  **Prioritas #1: Isi Data `tingkat` & `penjelasan`**
    *   **Tingkat Kesulitan:** Ya, ujian EPS-TOPIK memang memiliki tingkat kesulitan yang bervariasi. Namun, untuk **pola randomisasi yang akurat**, kita perlu menetapkan *kriteria* kesulitan untuk setiap soal. Tanpa data ini, bot akan kesulitan membedakan soal mudah/sedang/sulit.
    *   **Penjelasan Jawaban:** Ini bisa kita tangani dengan AI, tapi akan **memakan waktu & biaya**. Untuk MVP (Minimum Viable Product), kita bisa mulai dengan:
        *   Mengisi `penjelasan` secara manual (jika hanya sedikit).
        *   Mengambil penjelasan dari sumber lain jika tersedia.
        *   Atau, **membiarkan kolom `penjelasan` kosong dulu**, nanti bisa diisi belakangan.

2.  **Prioritas #2: Riset Standar EPS-TOPIK**
    *   Ini akan dilakukan oleh saya untuk menentukan proporsi soal & skor lulus.

3.  **Prioritas #3: Implementasi Fitur `Simulation`**
    *   Setelah data `tingkat` & `penjelasan` siap, baru kita buat query & fungsi JS.

---

## 💡 TINDAKAN SEGERA:

### 1. Menentukan Tingkat Kesulitan Soal
Karena Anda belum punya data `tingkat` (`mudah`/`sedang`/`sulit`) untuk setiap soal, dan ini krusial untuk randomisasi `Simulation`, kita perlu **menentukannya terlebih dahulu**.

**Opsi Pengisian Tingkat Kesulitan:**

*   **A. Manual di Supabase:** Anda bisa buka tabel `soal_eps` di Supabase, lalu isi kolom `tingkat` secara manual untuk setiap soal. Ini akurat tapi memakan waktu jika soalnya banyak.
*   **B. Otomatis Berdasarkan Urutan/Bab:** Kita bisa buat script sederhana yang mengasumsikan:
    *   Soal di bab-bab awal (1-20) → `mudah`
    *   Soal di bab tengah (21-40) → `sedang`
    *   Soal di bab akhir (41-60) → `sulit`
    Ini tidak 100% akurat, tapi bisa jadi **mulai yang baik**.
*   **C. Menggunakan AI (Untuk Penjelasan, bukan Tingkat):** Anda minta saya isi penjelasan, tapi ini **tidak bisa untuk menentukan tingkat kesulitan**. Tingkat kesulitan lebih ke analisis soal, bukan sekadar penjelasan.

### 2. Menangani Kolom `penjelasan`

Anda benar, mengisi penjelasan untuk ratusan soal itu sangat banyak. Untuk awal, kita bisa pilih salah satu:
*   **Kosongkan Dulu:** Kita fokus pada fungsionalitas simulasi dulu. Kolom `penjelasan` bisa diisi nanti.
*   **Gunakan AI (Opsional & Berbayar):** Jika Anda ingin penjelasan otomatis, ini perlu penanganan khusus karena melibatkan API call ke AI (misal: Claude, GPT). Ini di luar cakupan script Python standar.

---

## ❓ PERTANYAAN UNTUK ANDA:

1.  **Bagaimana Anda ingin menentukan `tingkat` kesulitan untuk setiap soal?**
    *   Manual di Supabase?
    *   Otomatis berdasarkan urutan bab (mudah/sedang/sulit)?
    *   Atau ada metode lain?

2.  **Untuk kolom `penjelasan`**: Apakah kita biarkan kosong dulu saja untuk fokus ke fitur simulasi?

Setelah kita punya data `tingkat` yang cukup, saya bisa buatkan:
- Query database untuk randomisasi soal simulasi.
- Script untuk halaman `simulasi.html`.
- Tabel `simulasi_hasil` (jika perlu).

Mohon informasinya agar saya bisa melanjutkan!