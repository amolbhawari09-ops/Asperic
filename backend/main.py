import os
import sys
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# === CORE COMPONENTS ===
from encoder import AspericEncoder
from predictor import Predictor
from situation_interpreter import SituationInterpreter
from reasoning_controller import ReasoningController
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
    version="3.1.2",  # Bumping version for the fix
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
    thinking: str = "practical"
    output: str = "simple"


# =========================
# BOOTSTRAP CORE
# =========================
print("🚀 BOOTING ASPERIC SOVEREIGN CORE...")

_ = embedding_provider.model
print("✅ EMBEDDING MODEL PRE-WARMED")

encoder = AspericEncoder()
predictor = Predictor()
reasoning_controller = ReasoningController()
situation_interpreter = SituationInterpreter()
memory = SupabaseMemory()
brain = AstraBrain(memory_shared=memory)

print("✅ SYSTEM CORE ONLINE")


# =========================
# RESPONSE NORMALIZER (CRITICAL)
# =========================
def normalize_assistant_text(brain_response: dict) -> str:
    """
    Guarantees a non-empty string for DB persistence.
    """
    if not isinstance(brain_response, dict):
        return str(brain_response)

    # Normal answer
    if isinstance(brain_response.get("answer"), str) and brain_response["answer"].strip():
        return brain_response["answer"].strip()

    # Refusal case
    if brain_response.get("status") == "REFUSED":
        refusal = brain_response.get("refusal", {})
        reason = refusal.get("reason", "Request refused.")
        return f"[REFUSED] {reason}"

    # Fallback (should never be hit, but safe)
    return "[SYSTEM] No response generated."


# =========================
# MAIN ENDPOINT (UPGRADED)
# =========================
@app.post("/ask")
async def handle_request(request: QueryRequest):
    """
    FINAL ORCHESTRATION PIPELINE:
    Encoder → Predictor → SituationInterpreter
           → ReasoningController → AstraBrain → OutputSystem
    """
    try:
        # =========================
        # 1. SECURITY GATE
        # =========================
        security = encoder.process_input(request.user_query)

        if security["status"] == "BLOCK":
            output_sys = OutputSystem(audience="CONSUMER")
            block_response = {
                "answer": security.get("reason", "Request blocked."),
                "status": "BLOCKED",
                "confidence": 1.0,
                "reasoning_depth": None,
                "assumptions": [],
                "limits": [],
                "next_steps": []
            }
            return output_sys.assemble(block_response, request.user_query)

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
        # 3. RISK CLASSIFICATION
        # =========================
        intent_signal = predictor.predict(clean_query)

        # =========================
        # 4. POLICY INTERPRETATION
        # =========================
        situation = situation_interpreter.interpret(
            predictor_output=intent_signal
        )

        # =========================
        # 5. REASONING DEPTH (FIXED SECTION 🛠️)
        # =========================
        raw_decision = reasoning_controller.decide(clean_query)
        
        # FIX: The "Anti-Crash" Converter
        # This guarantees reasoning_decision is ALWAYS a dictionary, never an object.
        if hasattr(raw_decision, "model_dump"):
            reasoning_decision = raw_decision.model_dump()
        elif hasattr(raw_decision, "dict"):
            reasoning_decision = raw_decision.dict()
        elif isinstance(raw_decision, dict):
            reasoning_decision = raw_decision
        else:
            # Fallback for weird objects
            reasoning_decision = {"depth": "standard", "thinking": "practical"}

        # =========================
        # 6. PROFESSIONAL REASONING
        # =========================
        brain_response = brain.chat(
            user_question=clean_query,
            history=history,
            situation=situation,
            reasoning_decision=reasoning_decision
        )

        print(f"🧠 Brain Response Type: {type(brain_response)}")
        # print(f"🧠 Brain Response: {str(brain_response)[:200]}")

        # =========================
        # 7. MEMORY PERSISTENCE (SAFE)
        # =========================
        memory.save_message(chat_id, "user", request.user_query)

        assistant_text = normalize_assistant_text(brain_response)
        
        print(f"✅ Normalized Assistant Text: {assistant_text[:200]}")

        memory.save_message(chat_id, "assistant", assistant_text)
        memory.ingest_interaction(
            request.user_id,
            request.user_query,
            assistant_text
        )

        # =========================
        # 8. OUTPUT RENDERING (FIXED) ✅
        # =========================
        
        # ✅ FIX: Build clean response dict with string answer
        clean_response = {
            "answer": assistant_text,
            "session_id": chat_id, # ✅ ADDED: Sends ID to frontend to fix URL issues
            "status": brain_response.get("status", "SUCCESS"),
            "confidence": brain_response.get("confidence", 0.5),
            "reasoning_depth": reasoning_decision.get("depth", "NONE"), # This is now safe
            "assumptions": brain_response.get("assumptions", []),
            "limits": brain_response.get("limits", []),
            "next_steps": brain_response.get("next_steps", [])
        }

        print(f"📦 Clean Response: {clean_response}")

        audience = (
            "ENTERPRISE"
            if situation.ruleset == "strict"
            else "CONSUMER"
        )

        output_sys = OutputSystem(audience=audience)

        final_output = output_sys.assemble(
            clean_response,
            request.user_query
        )
        
        # Ensure session_id is in the final output even after assembly
        if isinstance(final_output, dict):
            final_output["session_id"] = chat_id
        
        print(f"🎯 Final Output: {final_output}")

        return final_output

    except Exception as e:
        print(f"❌ CRITICAL NODE FAILURE: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # ✅ FIX: Return proper error response
        output_sys = OutputSystem(audience="CONSUMER")
        error_response = {
            "answer": f"System error: {str(e)}",
            "status": "ERROR",
            "confidence": 0.0,
            "reasoning_depth": None,
            "assumptions": [],
            "limits": [],
            "next_steps": []
        }
        return output_sys.assemble(error_response, request.user_query)


# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "version": "3.1.2",
        "timestamp": import_datetime()
    }


def import_datetime():
    import datetime
    return datetime.datetime.utcnow().isoformat()


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
