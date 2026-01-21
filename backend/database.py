import os
from supabase import create_client, Client

class SupabaseMemory:
    def __init__(self):
        # REPLACE THESE WITH YOUR ACTUAL SUPABASE KEYS
        # In Antigravity, set these in your Environment Variables or paste them here temporarily
        url = os.getenv("SUPABASE_URL", "https://jvaoecdczvkbmiwbdwxo.supabase.co")
        key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp2YW9lY2RjenZrYm1pd2Jkd3hvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg0MzY2MDgsImV4cCI6MjA4NDAxMjYwOH0.L9WJuc3feQXoh3oheqe-wdoMiXN53HMv1QxNBhugf48")
        self.supabase: Client = create_client(url, key)

    def get_history(self, chat_id):
        """Fetches memory for a specific chat ID"""
        try:
            response = self.supabase.table("messages")\
                .select("role, content")\
                .eq("chat_id", chat_id)\
                .order("created_at")\
                .limit(20)\
                .execute()
            return [{"role": m['role'], "content": m['content']} for m in response.data]
        except Exception as e:
            print(f"⚠️ DB Read Error: {e}")
            return []

    def save_message(self, chat_id, role, content):
        """Saves a thought to the cloud."""
        try:
            self.supabase.table("messages").insert({
                "chat_id": chat_id,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            print(f"⚠️ DB Save Error: {e}")

    def create_or_get_chat(self, user_id, project_id="general"):
        """Ensures a chat session exists"""
        # Try to find existing chat
        res = self.supabase.table("chats").select("id")\
            .eq("user_id", user_id)\
            .eq("project_id", project_id)\
            .execute()
        
        if res.data:
            return res.data[0]['id']
        
        # Create new if not found
        res = self.supabase.table("chats").insert({
            "user_id": user_id, 
            "project_id": project_id
        }).execute()
        return res.data[0]['id']
