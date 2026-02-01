import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables BEFORE anything else
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# === INTERNAL SOVEREIGN IMPORTS ===
from encoder import AspericEncoder
from predictor import Predictor
from astra_brain import AstraBrain
from memory import SupabaseMemory
from output_system import OutputSystem
from model_loader import embedding_provider  # Singleton pre-warm


# =========================
# SYSTEM INIT
# =========================
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

app = FastAPI(
    title="Asperic Sovereign Intelligence Node",
    version="2.1.0",  # Thinking + Output wired
    default_response_class=PlainTextResponse
)

# =========================
# SECURITY: CORS
# =========================
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# =========================
# REQUEST MODEL
# =========================
class QueryRequest(BaseModel):
    user_query: str
    user_id: str = "user_1"
    project_id: str = "general"

    # NEW (from frontend toggles)
    thinking: str = "practical"       # practical | analytical
    output: str = "simple"             # simple | professional

    # Legacy / internal
    mode: str = "auto"


# =========================
# BOOTSTRAP CORE
# =========================
print("🚀 BOOTING ASPERIC SOVEREIGN CORE...")

_ = embedding_provider.model
print("✅ EMBEDDING MODEL PRE-WARMED")

encoder = AspericEncoder()
router = Predictor()
memory = SupabaseMemory()
brain = AstraBrain(memory_shared=memory)

print("✅ SYSTEM CORE ONLINE")


# =========================
# MAIN ENDPOINT
# =========================
@app.post("/ask")
async def handle_request(request: QueryRequest):
    """
    EXECUTIVE PIPELINE:
    Security → Intent → Reasoning → Output
    """
    try:
        # --- STEP 1: SECURITY GATE ---
        security = encoder.process_input(request.user_query)
        if security["status"] == "BLOCK":
            output_sys = OutputSystem(audience="CONSUMER")
            refusal = {
                "status": "REFUSED",
                "refusal": {
                    "reason": "Security policy violation detected.",
                    "needed": ["Rephrase the request safely"],
                    "why_it_matters": "Unsafe inputs cannot be processed."
                }
            }
            return output_sys.assemble(refusal, request.user_query)

        clean_query = security["content"]

        # --- STEP 2: SESSION CONTEXT ---
        chat_id = memory.create_or_get_chat(request.user_id, request.project_id)
        history = memory.get_history(chat_id)

        # --- STEP 3: INTENT ROUTING (LEGACY, STILL VALID) ---
        if request.mode.upper() in ["RESEARCH", "DEEP", "PROJECT"]:
            mode = f"{request.mode.upper()}_MODE"
        else:
            mode, _ = router.predict(clean_query)

        # --- STEP 4: THINKING MODE NORMALIZATION ---
        thinking = request.thinking.lower()
        if thinking not in ["practical", "analytical"]:
            thinking = "practical"

        # --- STEP 5: BRAIN EXECUTION ---
        brain_response = brain.chat(
            clean_query,
            history=history,
            mode=mode,
            thinking=thinking
        )

        # --- STEP 6: MEMORY PERSISTENCE ---
        memory.save_message(chat_id, "user", request.user_query)

        assistant_text = brain_response.get("answer") or str(brain_response)
        memory.save_message(chat_id, "assistant", assistant_text)
        memory.ingest_interaction(
            request.user_id,
            request.user_query,
            assistant_text
        )

        # --- STEP 7: OUTPUT MODE NORMALIZATION ---
        audience = (
            "ENTERPRISE"
            if request.output.lower() == "professional"
            else "CONSUMER"
        )

        output_sys = OutputSystem(audience=audience)

        # --- STEP 8: FINAL OUTPUT ---
        return output_sys.assemble(brain_response, request.user_query)

    except Exception as e:
        print(f"❌ CRITICAL NODE FAILURE: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"NODE_ERROR: {str(e)}"
        )


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)