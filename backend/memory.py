import os
import json
from supabase import create_client
from model_loader import embedding_provider  # SINGLETON: Shared embedding model
from groq import Groq

class SupabaseMemory:
    def __init__(self):
        # 1. Supabase Connection (Data Layer)
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
             print("⚠️ MEMORY: Supabase credentials missing services.")
             self.client = None
        else:
             self.client = create_client(self.url, self.key)
             print("✅ MEMORY: Connected to Supabase.")

        # 2. Local Embeddings (Vector Layer) — USES SINGLETON
        self.embedder = embedding_provider
        
        # 3. Groq (Scout) for Classification
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"

    def create_or_get_chat(self, user_id, project_id):
        """Creates a chat session if not exists."""
        if not self.client: return "local_chat_id"
        res = self.client.table("chats").select("id").eq("user_id", user_id).eq("title", project_id).execute()
        if res.data: return res.data[0]['id']
        
        new_chat = self.client.table("chats").insert({
            "user_id": user_id, "title": project_id
        }).execute()
        return new_chat.data[0]['id']

    def save_message(self, chat_id, role, content):
        if not self.client: return
        self.client.table("messages").insert({
            "chat_id": chat_id, "role": role, "content": content
        }).execute()

    def ingest_interaction(self, user_id, user_q, ai_a):
        """
        Step 1: Classify (Scout)
        Step 2: Embed (Local LLaMA)
        Step 3: Store (Supabase)
        """
        classification = self._classify_interaction(user_q, ai_a)
        
        if classification.get("is_memory_worthy"):
            print(f"💎 MEMORY FOUND: {classification['content']}")
            self._store_memory(user_id, classification['content'], classification['type'])

    def _classify_interaction(self, user_q, assistant_a):
        # Determine if we should save this using Scout
        prompt = f"""
        Analyze this interaction. Is there a Fact, Preference, or Decision?
        USER: {user_q}
        AI: {assistant_a}
        Return JSON: {{ "is_memory_worthy": bool, "type": "fact", "content": "summary" }}
        """
        try:
            completion = self.groq.chat.completions.create(
                model=self.SCOUT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except:
            return {"is_memory_worthy": False}

    def _store_memory(self, user_id, content, mem_type):
        try:
            # Generate 384-dim vector LOCALLY
            vector = self.embedder.embed(content)
            
            self.client.table("memories").insert({
                "user_id": user_id,
                "content": content,
                "type": mem_type,
                "embedding": vector
            }).execute()
            print("✅ MEMORY SAFEGUARDED (Local Vector).")
        except Exception as e:
            print(f"❌ Storage Error: {e}")

    def search(self, query, user_id):
        """Semantic Retrieval using Local Embeddings."""
        if not self.client: return ""
        try:
            # Generate 384-dim vector LOCALLY
            query_vector = self.embedder.embed(query)
            
            # RPC Call (must match 384 dim schema)
            params = {
                "query_embedding": query_vector,
                "match_threshold": 0.5, # Lower threshold for 384-dim (typically)
                "match_count": 5,
                "user_id_param": user_id
            }
            res = self.client.rpc("match_memories", params).execute()
            
            if not res.data: return ""
            
            memory_block = "\n".join([f"- [{m.get('type','MEM').upper()}]: {m['content']}" for m in res.data])
            return f"LONG-TERM MEMORY:\n{memory_block}"
        except Exception as e:
            print(f"⚠️ Retrieval Error: {e}")
            return ""

    def get_history(self, chat_id):
        if not self.client: return []
        res = self.client.table("messages").select("*").eq("chat_id", chat_id).order("created_at", desc=True).limit(10).execute()
        return res.data[::-1] if res.data else []

    def generate_title_auto(self, chat_id, user_q, ai_a):
        """Generates a concise 3-4 word title using Scout and updates the chat."""
        if not self.client: return

        prompt = f"""
        Generate a concise, professional title (3-5 words max) for this chat session. 
        NO intro, NO quotes. Just the title.
        User: {user_q}
        AI: {ai_a}
        Title:
        """
        try:
            completion = self.groq.chat.completions.create(
                model=self.SCOUT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, # Slightly creative but focused
                max_tokens=20
            )
            title = completion.choices[0].message.content.strip().replace('"', '')
            
            # Update Supabase
            self.client.table("chats").update({"title": title}).eq("id", chat_id).execute()
            print(f"✨ CHAT RENAMED: {title}")
        except Exception as e:
            print(f"⚠️ Title Gen Error: {e}")

