-- Skema SQL untuk tabel soal_eps
-- Jalankan ini di SQL Editor Supabase (https://supabase.com/project/YOUR_PROJECT/sql)

create table if not exists public.soal_eps (
    id text primary key,
    bab integer not null,
    tipe text not null check (tipe in ('membaca', 'mendengarkan')),
    teks_soal text not null,
    gambar_url text default '',
    audio_url text default '',
    pilihan_a text default '',
    pilihan_b text default '',
    pilihan_c text default '',
    pilihan_d text default '',
    jawaban_benar text check (jawaban_benar in ('a', 'b', 'c', 'd')),
    audio_teks text default '',
    penjelasan text default '',
    tingkat text default 'sedang' check (tingkat in ('mudah', 'sedang', 'sulit')),
    akses text default 'free' check (akses in ('free', 'premium')),
    sumber_url text default '',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Enable Row Level Security (RLS)
alter table public.soal_eps enable row level security;

-- Policy: Everyone can read (public data)
create policy if not exists "Public read access" on public.soal_eps
    for select using (true);

-- Policy: Only authenticated can update
create policy if not exists "Authenticated update" on public.soal_eps
    for update using (auth.role() = 'authenticated');

-- Index untuk performa
create index if not exists idx_soal_eps_bab on public.soal_eps (bab);
create index if not exists idx_soal_eps_tipe on public.soal_eps (tipe);
create index if not exists idx_soal_eps_akses on public.soal_eps (akses);

-- Contoh data (opsional, bisa dihapus)
-- insert into public.soal_eps (id, bab, tipe, teks_soal, pilihan_a, pilihan_b, pilihan_c, pilihan_d, jawaban_benar)
-- values ('u31_m1', 31, 'membaca', 'Teks soal...', 'Pilihan A', 'Pilihan B', 'Pilihan C', 'Pilihan D', 'a');
