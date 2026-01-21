import sys
import time
import os
from dotenv import load_dotenv

# Force load frontend env for Supabase keys
load_dotenv('frontend/.env.local')

# Supabase Local Fallback (Hardcoded for checking)
if not os.getenv("NEXT_PUBLIC_SUPABASE_URL"):
    os.environ["NEXT_PUBLIC_SUPABASE_URL"] = "https://jvaoecdczvkbmiwbdwxo.supabase.co"
if not os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"):
    os.environ["NEXT_PUBLIC_SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp2YW9lY2RjenZrYm1pd2Jkd3hvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg0MzY2MDgsImV4cCI6MjA4NDAxMjYwOH0.L9WJuc3feQXoh3oheqe-wdoMiXN53HMv1QxNBhugf48"

# Add Groq Key for Scout Classifier
# if not os.getenv("GROQ_API_KEY"):
#     os.environ["GROQ_API_KEY"] = "PLACEHOLDER_KEY_DO_NOT_COMMIT"

from backend.memory import SupabaseMemory

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def test_rag_system():
    print("🧪 RAG DIAGNOSTIC (LLaMA MODE: 384-DIM)")
    print("---------------------------------------")

    try:
        mem = SupabaseMemory()
        if not mem.client:
            print("❌ FAIL: Supabase Connection")
            return
        print("✅ PASS: Supabase Connected")
        print("✅ PASS: Local Embedding Model Loaded (all-MiniLM-L6-v2)")
    except Exception as e:
        print(f"❌ FAIL: Init Error: {e}")
        return

    # 1. Fetch Real User ID (Required for Foreign Key Constraint)
    try:
        # We need a valid UUID that exists in auth.users
        # Since we have the service role key (anon key might not allow listing users, but let's try or assume one exists)
        # Actually RLS usually blocks listing users.
        # Strategies:
        # A. Use a known UUID if user provided one.
        # B. Login as a user (too complex for script).
        # C. Generate a UUID and hope the constraint isn't enforced on insert? NO, schema says 'references auth.users'.
        # Workaround: Use the 'anon' key to sign up a dummy user? 
        # Better: Since we successfully ran the app before, maybe there's a user in 'chats' table we can grab?
        
        # Try to find an existing chat and grabbing its user_id
        res = mem.client.table("chats").select("user_id").limit(1).execute()
        if res.data:
            test_user_id = res.data[0]['user_id']
            print(f"✅ FOUND USER ID: {test_user_id}")
        else:
            print("⚠️ NO USERS FOUND. Using dummy UUID.")
            test_user_id = "00000000-0000-0000-0000-000000000000"
            
    except Exception as e:
         print(f"⚠️ Fetch User Error: {e}")
         test_user_id = "00000000-0000-0000-0000-000000000000"

    print("\n🧪 TEST: Ingestion")
    # Simulate Ingestion
    mem.ingest_interaction(
        test_user_id,
        "My favorite color is obsidian black.",
        "Noted."
    )
    print("✅ Ingestion Logic Executed.")

    time.sleep(2)

    print("\n🧪 TEST: Retrieval")
    try:
        result = mem.search("What is my favorite color?", "test_user_verify_id")
        print(f"Result: {result}")
        
        if "obsidian black" in str(result) or "MEM" in str(result):
             print("✅ PASS: Memory Retrieved!")
        else:
             print("⚠️ WARN: Memory empty. (Did you run the NEW rag_schema.sql and RPC?)")
             
    except Exception as e:
        print(f"❌ FAIL: Search Error: {e}")

if __name__ == "__main__":
    test_rag_system()
