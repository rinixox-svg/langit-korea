#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"URL: {SUPABASE_URL}")
    print(f"Key (first 20 chars): {SUPABASE_ANON_KEY[:20] if SUPABASE_ANON_KEY else 'NOT FOUND'}")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("Missing credentials")
        exit(1)
    
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("✅ Connected!")
    
    # Test upload a small file
    test_path = Path("test_upload.txt")
    test_path.write_text("test")
    
    with open(test_path, "rb") as f:
        data = f.read()
    
    try:
        res = client.storage.from_("gambar-materi").upload(
            path="test.txt",
            file=data,
            file_options={"content-type": "text/plain", "upsert": "true"}
        )
        print(f"✅ Upload test success: {res}")
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
    
    test_path.unlink()  # Delete test file
    
except ImportError:
    print("❌ supabase not installed")
except Exception as e:
    print(f"❌ Error: {e}")
