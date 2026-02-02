import os
import sys
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# === CORE COMPONENTS ===
from encoder import AspericEncoder
from predictor import Predictor
from situation_interpreter import SituationInterpreter
from astra_brain import AstraBrain
from memory import SupabaseMemory
from output_system import OutputSystem
from model_loader import embedding_provider


# =========================
# SYSTEM INIT
# =========================
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

app = FastAPI(
    title="Asperic Sovereign Intelligence Node",
    version="3.0.0",
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


# =========================
# BOOTSTRAP CORE
# =========================
print("🚀 BOOTING ASPERIC SOVEREIGN CORE...")

_ = embedding_provider.model
print("✅ EMBEDDING MODEL PRE-WARMED")

encoder = AspericEncoder()
predictor = Predictor()
situation_interpreter = SituationInterpreter()
memory = SupabaseMemory()
brain = AstraBrain(memory_shared=memory)

print("✅ SYSTEM CORE ONLINE")


# =========================
# MAIN ENDPOINT
# =========================
@app.post("/ask")
async def handle_request(request: QueryRequest):
    """
    FINAL ORCHESTRATION PIPELINE:
    Encoder → Predictor → SituationInterpreter → AstraBrain → OutputSystem
    """
    try:
        # =========================
        # 1. SECURITY GATE
        # =========================
        security = encoder.process_input(request.user_query)

        if security["status"] == "REFUSED":
            output_sys = OutputSystem(audience="CONSUMER")
            return output_sys.assemble(security, request.user_query)

        clean_query = security["content"]

        # =========================
        # 2. MEMORY CONTEXT
        # =========================
        chat_id = memory.create_or_get_chat(
            request.user_id,
            request.project_id
        )
        history = memory.get_history(chat_id)

        # =========================
        # 3. INTENT CLASSIFICATION
        # =========================
        intent_signal = predictor.predict(clean_query)

        # =========================
        # 4. SITUATION INTERPRETATION
        # =========================
        situation = situation_interpreter.interpret(
            intent_signal=intent_signal,
            user_query=clean_query
        )

        # =========================
        # 5. PROFESSIONAL REASONING
        # =========================
        brain_response = brain.chat(
            user_question=clean_query,
            history=history,
            situation=situation
        )

        # =========================
        # 6. MEMORY PERSISTENCE
        # =========================
        memory.save_message(chat_id, "user", request.user_query)

        assistant_text = (
            brain_response.get("answer")
            if isinstance(brain_response, dict)
            else str(brain_response)
        )

        memory.save_message(chat_id, "assistant", assistant_text)
        memory.ingest_interaction(
            request.user_id,
            request.user_query,
            assistant_text
        )

        # =========================
        # 7. OUTPUT RENDERING
        # =========================
        audience = (
            "ENTERPRISE"
            if situation.ruleset == "strict"
            else "CONSUMER"
        )

        output_sys = OutputSystem(audience=audience)

        return output_sys.assemble(
            brain_response,
            request.user_query
        )

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