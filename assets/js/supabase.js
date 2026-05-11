// ==========================================
// LANGIT KOREA — Supabase Client Initialization
// ==========================================
// GANTI DENGAN MILIKMU

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

const SUPABASE_URL = "https://mozmuwrkfsipzfupybwh.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vem11d3JrZnNpcHpmdXB5YndoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzY5NTk1NCwiZXhwIjoyMDkzMjcxOTU0fQ.SZSNk6xV-vq17beo_LwWzsZSp9UVGdqfR-R35cGxawE";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
