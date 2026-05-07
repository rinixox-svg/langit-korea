#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print('SUPABASE_URL atau SUPABASE_ANON_KEY tidak ditemukan')
        exit(1)
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print('Koneksi Supabase OK')
except ImportError:
    print('Library supabase belum diinstall')
    exit(1)

print('Script integrasi siap')
