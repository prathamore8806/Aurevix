"""
Quick Supabase Connection Tester
Run: python test_supabase.py
"""

import sys
from pathlib import Path

# Fix Windows console UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

import supabase_manager

def main():
    print("=" * 60)
    print("☁️ Testing Aurevix Supabase Connection...")
    print("=" * 60)

    sm = supabase_manager.get_supabase()

    if not sm.is_configured():
        print("❌ Status: Credentials not configured yet in .env file.")
        print("👉 Please paste your SUPABASE_URL and SUPABASE_KEY in .env")
        return

    if not sm.is_connected:
        print("❌ Status: Failed to connect to Supabase.")
        return

    print("✅ SUCCESS! Connected to Supabase!")
    try:
        # Test querying tables
        res = sm.client.table("profiles").select("count", count="exact").execute()
        print(f"📊 PostgreSQL Database accessible! (Profiles count: {res.count})")
        print("🎉 Your cloud backend is 100% ready for Aurevix!")
    except Exception as e:
        print(f"⚠️ Connected, but table query returned: {e}")

if __name__ == "__main__":
    main()
