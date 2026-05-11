-- Setup latihan_interaktif table for Langit Korea
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.latihan_interaktif (
    id BIGSERIAL PRIMARY KEY,
    unit INTEGER NOT NULL UNIQUE,
    vocab1 JSONB DEFAULT '[]',
    grammar1 JSONB DEFAULT '[]',
    conversation1 JSONB DEFAULT '[]',
    vocab2 JSONB DEFAULT '[]',
    grammar2 JSONB DEFAULT '[]',
    conversation2 JSONB DEFAULT '[]',
    budaya JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.latihan_interaktif ENABLE ROW LEVEL SECURITY;

-- Allow anon key to read
CREATE POLICY "Allow read" ON public.latihan_interaktif
    FOR SELECT USING (true);

-- Only service role can insert/update
CREATE POLICY "Allow service insert" ON public.latihan_interaktif
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow service update" ON public.latihan_interaktif
    FOR UPDATE USING (true);

-- Index on unit
CREATE INDEX IF NOT EXISTS idx_latihan_interaktif_unit ON public.latihan_interaktif(unit);
