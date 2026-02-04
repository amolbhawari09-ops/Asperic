import os
import json
from supabase import create_client
from groq import Groq
from model_loader import embedding_provider


class SupabaseMemory:
    """
    Asperic Memory Layer (Hardened)
    --------------------------------
    Responsibilities:
    - Persist chat messages (strict, safe)
    - Persist long-term memories (vectorized)
    - NEVER store invalid or null content
    - NEVER crash the system
    """

    # =========================
    # INIT
    # =========================
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            print("⚠️ MEMORY: Supabase credentials missing. Running in NO-PERSIST mode.")
            self.client = None
        else:
            self.client = create_client(self.url, self.key)
            print("✅ MEMORY: Connected to Supabase.")

        self.embedder = embedding_provider

        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"

    # =========================
    # CHAT SESSION
    # =========================
    def create_or_get_chat(self, user_id: str, project_id: str):
        if not self.client:
            return "local_chat_id"

        res = (
            self.client
            .table("chats")
            .select("id")
            .eq("user_id", user_id)
            .eq("title", project_id)
            .execute()
        )

        if res.data:
            return res.data[0]["id"]

        created = self.client.table("chats").insert({
            "user_id": user_id,
            "title": project_id
        }).execute()

        return created.data[0]["id"]

    # =========================
    # MESSAGE PERSISTENCE (CRITICAL)
    # =========================
    def save_message(self, chat_id: str, role: str, content):
        """
        Saves a chat message.
        GUARANTEES:
        - content is a non-empty string
        - never throws
        """
        if not self.client:
            return

        text = self._normalize_content(content)
        if not text:
            # Absolute safety net
            text = "[SYSTEM] Empty message suppressed."

        try:
            self.client.table("messages").insert({
                "chat_id": chat_id,
                "role": role,
                "content": text
            }).execute()
        except Exception as e:
            print(f"⚠️ MEMORY: Failed to save message: {e}")

    # =========================
    # LONG-TERM MEMORY INGESTION
    # =========================
    def ingest_interaction(self, user_id: str, user_q: str, ai_a: str):
        if not self.client:
            return

        ai_text = self._normalize_content(ai_a)
        if not ai_text:
            return

        classification = self._classify_interaction(user_q, ai_text)
        if not classification.get("is_memory_worthy"):
            return

        content = classification.get("content", "").strip()
        mem_type = classification.get("type", "fact")

        if content:
            self._store_memory(user_id, content, mem_type)

    # =========================
    # CLASSIFICATION
    # =========================
    def _classify_interaction(self, user_q: str, assistant_a: str) -> dict:
        prompt = f"""
Analyze this interaction. Decide if it contains a stable Fact, Preference, or Decision.

USER: {user_q}
AI: {assistant_a}

Return JSON only:
{{ "is_memory_worthy": bool, "type": "fact|preference|decision", "content": "short summary" }}
"""
        try:
            completion = self.groq.chat.completions.create(
                model=self.SCOUT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(f"⚠️ MEMORY: Classification failed: {e}")
            return {"is_memory_worthy": False}

    # =========================
    # VECTOR STORAGE
    # =========================
    def _store_memory(self, user_id: str, content: str, mem_type: str):
        if not self.client:
            return

        try:
            vector = self.embedder.embed(content)

            self.client.table("memories").insert({
                "user_id": user_id,
                "content": content,
                "type": mem_type,
                "embedding": vector
            }).execute()

            print("✅ MEMORY: Long-term memory stored.")

        except Exception as e:
            print(f"⚠️ MEMORY: Vector storage failed: {e}")

    # =========================
    # RETRIEVAL
    # =========================
    def search(self, query: str, user_id: str) -> str:
        if not self.client:
            return ""

        try:
            query_vector = self.embedder.embed(query)

            params = {
                "query_embedding": query_vector,
                "match_threshold": 0.5,
                "match_count": 5,
                "user_id_param": user_id
            }

            res = self.client.rpc("match_memories", params).execute()
            if not res.data:
                return ""

            return "LONG-TERM MEMORY:\n" + "\n".join(
                f"- [{m.get('type','MEM').upper()}]: {m['content']}"
                for m in res.data
            )

        except Exception as e:
            print(f"⚠️ MEMORY: Retrieval failed: {e}")
            return ""

    # =========================
    # HISTORY
    # =========================
    def get_history(self, chat_id: str):
        if not self.client:
            return []

        try:
            res = (
                self.client
                .table("messages")
                .select("role, content")
                .eq("chat_id", chat_id)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            return res.data[::-1] if res.data else []
        except Exception as e:
            print(f"⚠️ MEMORY: History read failed: {e}")
            return []

    # =========================
    # UTIL
    # =========================
    def _normalize_content(self, content) -> str:
        if not content:
            return ""
        if not isinstance(content, str):
            return str(content)
        return content.strip()