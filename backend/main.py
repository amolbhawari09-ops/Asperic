import os
import sys
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# === CORE COMPONENTS ===
from encoder import AspericEncoder
from predictor import Predictor
from situation_interpreter import SituationInterpreter
from reasoning_controller import ReasoningController
from astra_brain import AstraBrain
from semantic_engine import SemanticEngine
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
    version="4.0.0",  # 🚀 FULL COGNITION ACTIVATED
    default_response_class=JSONResponse
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
print("🚀 BOOTING ASPERIC FULL COGNITION CORE...")

_ = embedding_provider.model
print("✅ EMBEDDING MODEL PRE-WARMED")

encoder = AspericEncoder()
semantic_engine = SemanticEngine()
predictor = Predictor()
reasoning_controller = ReasoningController()
situation_interpreter = SituationInterpreter()
memory = SupabaseMemory()
brain = AstraBrain(memory_shared=memory)

print("🧠 SEMANTIC ENGINE ONLINE")
print("✅ SYSTEM CORE ONLINE")


# =========================
# RESPONSE NORMALIZER
# =========================
def normalize_assistant_text(brain_response: dict) -> str:
    if not isinstance(brain_response, dict):
        return str(brain_response)

    if isinstance(brain_response.get("answer"), str) and brain_response["answer"].strip():
        return brain_response["answer"].strip()

    if brain_response.get("status") == "REFUSED":
        refusal = brain_response.get("refusal", {})
        return f"[REFUSED] {refusal.get('reason', 'Request refused.')}"

    return "[SYSTEM] No response generated."


# =========================
# MAIN ENDPOINT
# =========================
@app.post("/ask")
async def handle_request(request: QueryRequest):
    """
    FULL ASPERIC COGNITION PIPELINE
    """
    try:
        # =========================
        # 1. SECURITY GATE
        # =========================
        security = encoder.process_input(request.user_query)

        if security["status"] == "BLOCK":
            output_sys = OutputSystem(audience="CONSUMER")
            return output_sys.assemble(
                {
                    "answer": security.get("reason", "Request blocked."),
                    "status": "BLOCKED",
                    "confidence": 1.0,
                    "reasoning_depth": None,
                    "assumptions": [],
                    "limits": [],
                    "next_steps": []
                },
                request.user_query
            )

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
        # 3. SEMANTIC ANALYSIS (🧠 CORE)
        # =========================
        semantic_profile = semantic_engine.analyze(clean_query)

        # =========================
        # 4. RISK CLASSIFICATION
        # =========================
        intent_signal = predictor.predict(clean_query)

        # =========================
        # 5. POLICY INTERPRETATION
        # =========================
        situation = situation_interpreter.interpret(
            predictor_output=intent_signal
        )

        # =========================
        # 6. SEMANTIC REASONING DEPTH
        # =========================
        reasoning_decision = reasoning_controller.decide(
            clean_query,
            semantic_profile
        )

        # =========================
        # 7. SEMANTIC REASONING EXECUTION
        # =========================
        brain_response = brain.chat(
            user_question=clean_query,
            history=history,
            situation=situation,
            reasoning_decision=reasoning_decision,
            semantic_profile=semantic_profile
        )

        # =========================
        # 8. MEMORY PERSISTENCE
        # =========================
        memory.save_message(chat_id, "user", request.user_query)

        assistant_text = normalize_assistant_text(brain_response)

        memory.save_message(chat_id, "assistant", assistant_text)
        memory.ingest_interaction(
            request.user_id,
            request.user_query,
            assistant_text
        )

        # =========================
        # 9. OUTPUT RENDERING
        # =========================
        clean_response = {
            "answer": assistant_text,
            "session_id": chat_id,
            "status": brain_response.get("status", "SUCCESS"),
            "confidence": brain_response.get("confidence", 0.5),
            "reasoning_depth": reasoning_decision.depth,
            "assumptions": brain_response.get("assumptions", []),
            "limits": brain_response.get("limits", []),
            "next_steps": brain_response.get("next_steps", [])
        }

        audience = (
            "ENTERPRISE"
            if situation.ruleset == "strict"
            else "CONSUMER"
        )

        output_sys = OutputSystem(audience=audience)
        final_output = output_sys.assemble(clean_response, request.user_query)

        final_output["session_id"] = chat_id
        final_output["semantic_profile"] = semantic_profile  # optional but useful

        return final_output

    except Exception as e:
        print(f"❌ CRITICAL NODE FAILURE: {str(e)}")
        import traceback
        traceback.print_exc()

        output_sys = OutputSystem(audience="CONSUMER")
        return output_sys.assemble(
            {
                "answer": f"System error: {str(e)}",
                "status": "ERROR",
                "confidence": 0.0,
                "reasoning_depth": None,
                "assumptions": [],
                "limits": [],
                "next_steps": []
            },
            request.user_query
        )


# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
async def health_check():
    import datetime
    return {
        "status": "online",
        "version": "4.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)