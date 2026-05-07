# Deployment Security Checklist untuk Langit Korea

## 🔐 1. API Keys & Credentials Security

### API Keys & Environment Variables
- ❌ **JANGAN** pernah hardcode API keys di client-side (file HTML/JS).
- ✅ Gunakan environment variables di platform deployment (Vercel).
- ✅ Simpan Supabase URL dan Anon Key di environment variables.
- ✅ Gunakan `.env` file untuk development lokal dan tambahkan ke `.gitignore`.
- ✅ **JANGAN** commit file sensitif (`.env`, `service-key.json`) ke repository.

### Supabase Security
- ✅ **Row Level Security (RLS)** untuk semua tabel **HARUS** diaktifkan.
- ✅ Set permissions dan policies yang sesuai untuk setiap table (lihat bagian 3).

### Authentication Security
- ✅ Email confirmation untuk user baru (aktifkan di Supabase Dashboard).
- ✅ Password complexity requirements (minimal 8 karakter, diatur di Supabase Auth).
- ✅ Session timeout handling (Supabase Auth menangani ini, pastikan refresh token berjalan).
- ✅ Secure password storage (Otomatis ditangani oleh Supabase Auth - jangan diubah).

## 🌐 2. Deployment & Hosting Security (Vercel)

### Vercel Security
- ✅ Gunakan Custom domain dengan HTTPS (Vercel menyediakan SSL gratis otomatis).
- ✅ Set Environment Variables di Vercel Dashboard (`Settings > Environment Variables`):
    - `SUPABASE_URL`
    - `SUPABASE_ANON_KEY`
- ✅ Aktifkan "Password Protection" atau "Trusted IPs" untuk Preview Deployments jika perlu.
- ✅ Pastikan `vercel.json` tidak mengekspos file sensitif.

### Rate Limiting
- ✅ Batasi request API untuk mencegah abuse (Gunakan Supabase Edge Functions jika perlu).
- ✅ Rate limit untuk login attempts (Supabase Auth sudah memiliki built-in protection).
- ✅ Batasi akses ke soal premium (Gunakan RLS, bukan hanya menyembunyikan tombol di UI).

## 🔒 3. Database & Data Security (Supabase RLS)

### Database Security
RLS (Row Level Security) adalah kunci keamanan data di Supabase. Berikut contoh policy untuk tabel Langit Korea:

#### Tabel `users`
```sql
-- User hanya bisa melihat dan mengupdate data mereka sendiri
CREATE POLICY "User can view own profile"
ON users FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "User can update own profile"
ON users FOR UPDATE
USING (auth.uid() = id);
```

#### Tabel `soal_eps`
```sql
-- Semua user (termasuk yang belum login) bisa baca soal 'free'
-- User login bisa baca 'premium' (logika premium di-handle di client/edge function)
CREATE POLICY "Public can read free questions"
ON soal_eps FOR SELECT
USING (akses = 'free');

-- Atau jika ingin lebih ketat (hanya user login yang bisa baca):
-- CREATE POLICY "Authenticated users can read questions"
-- ON soal_eps FOR SELECT
-- USING (auth.role() = 'authenticated');
```

#### Tabel `progress_user`
```sql
-- User hanya bisa insert/update progress milik sendiri
CREATE POLICY "User can insert own progress"
ON progress_user FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "User can view own progress"
ON progress_user FOR SELECT
USING (auth.uid() = user_id);
```

#### Tabel `simulasi_hasil`
```sql
-- User hanya bisa melihat hasil simulasi mereka sendiri
CREATE POLICY "User can view own results"
ON simulasi_hasil FOR SELECT
USING (auth.uid() = user_id);
```

### File Storage Security (Audio MP3)
- ✅ Gunakan Supabase Storage policies untuk audio files.
- ✅ Gunakan **Signed URLs** untuk akses file audio (berlaku sementara, misal 1 jam).
- ✅ Jangan izinkan akses public langsung ke bucket storage jika tidak perlu.

```sql
-- Contoh Policy Storage: Hanya user login yang bisa download
CREATE POLICY "Authenticated users can download audio"
ON storage.objects FOR SELECT
USING (bucket_id = 'audio-listening' AND auth.role() = 'authenticated');
```

## 🛡️ 4. Frontend Security (Vanilla JS)

### Client-side Validation
- ✅ **Validasi di Server-Side (Supabase RLS)** untuk semua operasi database (Jangan percaya client input).
- ✅ Sanitasi input dari user (hindari XSS). Karena kita pakai Vanilla JS, pastikan tidak memasukkan input user ke `innerHTML` secara langsung tanpa sanitasi.
- ✅ Gunakan `textContent` atau `innerText` daripada `innerHTML` jika tidak perlu render HTML.

### Content Security Policy (CSP)
Karena project ini menggunakan **Vanilla JS dengan satu file per halaman**, kita mungkin perlu menggunakan inline style/script. Berikut konfigurasi yang disarankan:

```html
<!-- Contoh meta tag CSP di setiap file HTML -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self';
               script-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com 'unsafe-inline';
               style-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com 'unsafe-inline';
               font-src 'self' https://fonts.gstatic.com;
               img-src 'self' data: https://*.supabase.co;
               connect-src 'self' https://*.supabase.co;">
```
*Catatan: `'unsafe-inline'` digunakan karena keterbatasan Vanilla JS tanpa build step. Pastikan logika aplikasi tetap aman.*

## 📁 5. File & Code Security

### File Structure
- ✅ Pastikan `.gitignore` berisi:
```gitignore
.env
node_modules/
*.log
.DS_Store
supabase/*.key
```
- ❌ JANGAN commit file berikut ke repository:
    - `.env` files
    - `supabase-config.js` yang berisi key asli (gunakan template)
    - `service-key.json` atau private keys
    - Folder `private/`

## 🎯 6. Environment Variables (Supabase)

Gunakan nama variabel yang standar:

```bash
# .env (untuk development lokal)
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# JANGAN TARUH SERVICE ROLE KEY DI FRONTEND/CLIENT-SIDE
```

Di Vercel, tambahkan sebagai Environment Variable:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

## 🚀 7. GitHub Actions & Automation Security

Jika menggunakan GitHub Actions untuk scraping otomatis (sesuai rencana):
- ✅ Simpan `SUPABASE_SERVICE_ROLE_KEY` di GitHub Secrets (`Settings > Secrets and variables > Actions`).
- ✅ Jangan print/log API Key di output GitHub Actions.
- ✅ Batasi akses repository jika berisi data sensitif.

## 📊 8. Security Monitoring
- ✅ Aktifkan "Logs" di Supabase Dashboard untuk memantau akses database yang mencurigakan.
- ✅ Gunakan Vercel Analytics/Monitoring untuk melihat traffic.
- ✅ Pastikan error handling di frontend tidak memunculkan detail teknis (stack trace) ke user.

---
*Langit Korea — Aman, Terarah, dan Penuh Harapan.*
