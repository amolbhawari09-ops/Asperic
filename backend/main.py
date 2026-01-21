import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE any other imports
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

# Internal Sovereign Node Imports - AUTHORITY BOUNDARIES
from encoder import AspericEncoder
from predictor import Predictor
from astra_brain import AstraBrain
from memory import SupabaseMemory
from model_loader import embedding_provider  # SINGLETON for pre-warming

# 1. SYSTEM INITIALIZATION & UNICODE FIX
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

app = FastAPI(
    title="Asperic Sovereign Intelligence Node",
    version="1.7.0",  # Version bump for performance fix
    default_response_class=PlainTextResponse
)

# 2. SECURITY: CORS POLICY (Production-Ready)
# Reads from environment; defaults to localhost for development
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    user_query: str
    user_id: str = "user_1"
    project_id: str = "general"
    mode: str = "auto"

# 3. COMPONENT BOOTSTRAP (Stateful Singletons with Dependency Injection)
print("🚀 BOOTING ASPERIC SOVEREIGN CORE...")

# Pre-warm the embedding model (singleton) so first request is fast
_ = embedding_provider.model
print("✅ EMBEDDING MODEL PRE-WARMED (Singleton)")

encoder = AspericEncoder()
router = Predictor()
memory = SupabaseMemory()  # Uses the singleton embedding_provider internally
brain = AstraBrain(memory_shared=memory)  # DEPENDENCY INJECTION: Shared memory
print("✅ SYSTEM CORE ONLINE.")

@app.post("/ask")
async def handle_request(request: QueryRequest):
    """
    EXECUTIVE PIPELINE:
    Orchestrates Security, Intent, Reasoning, and Final Assembly.
    """
    try:
        # STEP 1: SECURITY GATE (The Encoder)
        # Returns a structured status; main.py decides the terminal action.
        security_check = encoder.process_input(request.user_query)
        if security_check["status"] == "BLOCK":
            return "🛡️ SECURITY VIOLATION: Input rejected by Sovereign Shield."
        
        clean_query = security_check["content"]

        # STEP 2: SESSION RETRIEVAL
        chat_id = memory.create_or_get_chat(request.user_id, request.project_id)
        history = memory.get_history(chat_id)

        # STEP 3: INTENT ROUTING
        # Explicit mode request is honored; otherwise, Predictor determines intent.
        if request.mode.upper() in ["RESEARCH", "DEEP", "PROJECT"]:
            mode = f"{request.mode.upper()}_MODE"
        else:
            mode, confidence = router.predict(clean_query)

        # STEP 4: REASONING EXECUTION (The Brain)
        # Brain returns only the clean 'body' content.
        raw_body = brain.chat(clean_query, history=history, mode=mode)

        # STEP 5: ASYNC DATA PERSISTENCE
        memory.save_message(chat_id, "user", request.user_query)
        memory.save_message(chat_id, "assistant", raw_body)
        memory.ingest_interaction(request.user_id, request.user_query, raw_body)

        # STEP 6: STRUCTURAL ENVELOPE (Final Authority)
        # LLM never decides structure; it is added deterministically via code.
        return brain.assemble_output(raw_body, mode)

    except Exception as e:
        print(f"❌ CRITICAL NODE FAILURE: {str(e)}")
        # Returns proper HTTP 500 status for professional API consumption.
        raise HTTPException(status_code=500, detail=f"NODE_ERROR: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)