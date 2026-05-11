import os, requests
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Extract project ref
project_ref = SUPABASE_URL.replace("https://", "").split(".")[0]

# Supabase Management API (for direct DB access)
MGMT_URL = f"https://{project_ref}.supabase.co"
HEADERS = {
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "apikey": SUPABASE_SERVICE_KEY,
    "Content-Type": "application/json"
}

# Step 1: Drop old table
DROP_SQL = 'DROP TABLE IF EXISTS public.latihan_interaktif CASCADE;'
r = requests.post(
    f"{SUPABASE_URL}/rest/v1/rpc/exec",
    headers=HEADERS,
    json={"query": DROP_SQL},
    timeout=30
)
print(f"Drop table: {r.status_code}")

# Step 2: Create new table with proper schema
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS public.latihan_interaktif (
    id BIGSERIAL PRIMARY KEY,
    unit INTEGER NOT NULL,
    seksi TEXT NOT NULL,
    tipe_latihan TEXT NOT NULL,
    halaman INTEGER,
    vocab1 JSONB DEFAULT '[]'::jsonb,
    grammar1 JSONB DEFAULT '[]'::jsonb,
    conversation1 JSONB DEFAULT '[]'::jsonb,
    vocab2 JSONB DEFAULT '[]'::jsonb,
    grammar2 JSONB DEFAULT '[]'::jsonb,
    conversation2 JSONB DEFAULT '[]'::jsonb,
    budaya JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(unit, seksi, tipe_latihan)
);
"""
r2 = requests.post(
    f"{SUPABASE_URL}/rest/v1/rpc/exec",
    headers=HEADERS,
    json={"query": CREATE_SQL},
    timeout=30
)
print(f"Create table: {r2.status_code}")
if r2.status_code not in [200, 201, 204]:
    print(f"Create error: {r2.text[:300]}")

# Step 3: Enable RLS
RLS_SQL = """
ALTER TABLE public.latihan_interaktif ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow read" ON public.latihan_interaktif FOR SELECT USING (true);
CREATE POLICY "Allow insert" ON public.latihan_interaktif FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow update" ON public.latihan_interaktif FOR UPDATE USING (true);
CREATE POLICY "Allow delete" ON public.latihan_interaktif FOR DELETE USING (true);
"""
r3 = requests.post(
    f"{SUPABASE_URL}/rest/v1/rpc/exec",
    headers=HEADERS,
    json={"query": RLS_SQL},
    timeout=30
)
print(f"RLS: {r3.status_code}")

# Step 4: Create index
IDX_SQL = "CREATE INDEX IF NOT EXISTS idx_latihan_unit ON public.latihan_interaktif(unit);"
r4 = requests.post(
    f"{SUPABASE_URL}/rest/v1/rpc/exec",
    headers=HEADERS,
    json={"query": IDX_SQL},
    timeout=30
)
print(f"Index: {r4.status_code}")
