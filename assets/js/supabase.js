// ==========================================
// LANGIT KOREA — Supabase Client Initialization
// ==========================================
// GANTI DENGAN MILIKMU

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

const SUPABASE_URL = "https://mozmuwrkfsipzfupybwh.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vem11d3JrZnNpcHpmdXB5YndoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTU5NTQsImV4cCI6MjA5MzI3MTk1NH0.RPqu-07AyKygnS_bPhMO_IgXSz2r8jkljPc5TGq7Vzg";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
