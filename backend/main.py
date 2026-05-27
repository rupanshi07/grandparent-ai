from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from call_handler import (initiate_call, generate_greeting,
                          generate_response, generate_goodbye)
from conversation import get_ai_response
from database import (create_tables, add_elder, get_elder,
                      get_all_elders, update_attempt_status)
import os

load_dotenv()
create_tables()

app = FastAPI(title="Grandparent AI Companion")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversation history in memory during call
# Key: elder_id, Value: list of messages
active_conversations = {}

class ElderCreate(BaseModel):
    name: str
    phone_number: str
    language: str = "hindi"
    call_time: str = "09:00"
    family_contacts: list = []

# ─── BASIC ENDPOINTS ──────────────────────────────────────────
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Grandparent AI server is running!"}

@app.get("/")
def home():
    return {"project": "Grandparent AI Companion", "version": "1.0"}

@app.get("/check-keys")
def check_keys():
    return {
        "twilio": "✓ loaded" if os.getenv("TWILIO_ACCOUNT_SID") else "✗ missing",
        "groq": "✓ loaded" if os.getenv("GROQ_API_KEY") else "✗ missing",
        "elevenlabs": "✓ loaded" if os.getenv("ELEVENLABS_API_KEY") else "✗ missing",
    }

# ─── ELDER ENDPOINTS ──────────────────────────────────────────
@app.post("/elders")
def create_elder(elder: ElderCreate):
    try:
        new_elder = add_elder(
            name=elder.name,
            phone=elder.phone_number,
            language=elder.language,
            call_time=elder.call_time,
            family_contacts=elder.family_contacts
        )
        return {
            "message": f"Elder '{new_elder.name}' added!",
            "elder_id": new_elder.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/elders")
def list_elders():
    elders = get_all_elders()
    return {
        "total": len(elders),
        "elders": [
            {
                "id": e.id,
                "name": e.name,
                "phone": e.phone_number,
                "language": e.language,
                "call_time": e.call_time,
                "family_contacts": e.family_contacts,
                "memory_summary": e.memory_summary
            }
            for e in elders
        ]
    }

@app.get("/elders/{elder_id}")
def get_elder_by_id(elder_id: int):
    elder = get_elder(elder_id)
    if not elder:
        raise HTTPException(status_code=404, detail="Elder not found")
    return {
        "id": elder.id,
        "name": elder.name,
        "phone": elder.phone_number,
        "language": elder.language,
        "call_time": elder.call_time,
        "family_contacts": elder.family_contacts,
        "memory_summary": elder.memory_summary
    }

# ─── CALL ENDPOINTS ───────────────────────────────────────────
@app.get("/call/answer")
@app.post("/call/answer")
async def call_answer(request: Request):
    """
    Twilio calls this when elder picks up.
    We greet them and start listening.
    """
    # Default to elder_id 1 for now
    elder_id = 1
    elder = get_elder(elder_id)
    elder_name = elder.name if elder else "Dadi Ji"

    # Clear any old conversation for this elder
    active_conversations[elder_id] = []

    twiml = generate_greeting(elder_name, elder_id)
    return Response(content=twiml, media_type="text/xml")

@app.post("/call/respond/{elder_id}")
async def call_respond(elder_id: int, request: Request):
    """
    Twilio sends us what the elder said.
    We get AI response and speak it back.
    This is the CONVERSATION LOOP!
    """
    form_data = await request.form()
    elder_speech = form_data.get("SpeechResult", "")
    confidence = form_data.get("Confidence", "0")

    print(f"Elder said: '{elder_speech}' (confidence: {confidence})")

    # Get elder from database
    elder = get_elder(elder_id)
    if not elder:
        return Response(
            content=generate_goodbye("Dadi Ji"),
            media_type="text/xml"
        )

    # Get or create conversation history
    if elder_id not in active_conversations:
        active_conversations[elder_id] = []

    history = active_conversations[elder_id]

    # Check if elder wants to end call
    end_phrases = ["bye", "goodbye", "alvida", "band karo",
                   "rakhna", "theek hai bas", "bas karo"]
    if any(phrase in elder_speech.lower() for phrase in end_phrases):
        twiml = generate_goodbye(elder.name)
        active_conversations.pop(elder_id, None)
        return Response(content=twiml, media_type="text/xml")

    # Check conversation length — end after 8 exchanges
    if len(history) >= 16:
        twiml = generate_goodbye(elder.name)
        active_conversations.pop(elder_id, None)
        return Response(content=twiml, media_type="text/xml")

    # Get AI response
    try:
        ai_reply, updated_history = get_ai_response(
            elder_name=elder.name,
            language=elder.language,
            memory_summary=elder.memory_summary,
            conversation_history=history,
            user_message=elder_speech
        )
        active_conversations[elder_id] = updated_history
        print(f"AI replied: '{ai_reply}'")
    except Exception as e:
        print(f"AI error: {e}")
        ai_reply = "Mujhe thoda sun'ne mein takleef ho rahi hai. Kya aap dobara bol sakte hain?"

    twiml = generate_response(elder.name, elder_id, ai_reply)
    return Response(content=twiml, media_type="text/xml")

@app.post("/call/status")
async def call_status(request: Request):
    """Twilio sends call status updates here."""
    form_data = await request.form()
    status = form_data.get("CallStatus")
    sid = form_data.get("CallSid")
    print(f"Call {sid} status: {status}")
    update_attempt_status(sid, status)
    return {"status": "received"}

@app.post("/test/call")
async def test_call():
    """Triggers a test call."""
    phone = os.getenv("TEST_PHONE_NUMBER")
    if not phone:
        return {"error": "TEST_PHONE_NUMBER not set in .env"}
    call_sid = initiate_call(phone, "Dadi Ji")
    return {"message": "Call initiated!", "call_sid": call_sid}