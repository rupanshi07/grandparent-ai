from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from call_handler import initiate_call, generate_greeting
from database import (create_tables, add_elder, get_elder, 
                      get_all_elders, log_call_attempt, 
                      update_attempt_status)
import os

load_dotenv()

# Create database tables on startup
create_tables()

app = FastAPI(title="Grandparent AI Companion")

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── REQUEST MODELS ───────────────────────────────────────────
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
    return {
        "project": "Grandparent AI Companion",
        "version": "1.0",
        "status": "running"
    }

@app.get("/check-keys")
def check_keys():
    return {
        "twilio": "✓ loaded" if os.getenv("TWILIO_ACCOUNT_SID") else "✗ missing",
        "anthropic": "✓ loaded" if os.getenv("ANTHROPIC_API_KEY") else "✗ missing",
        "elevenlabs": "✓ loaded" if os.getenv("ELEVENLABS_API_KEY") else "✗ missing",
    }

# ─── ELDER ENDPOINTS ──────────────────────────────────────────
@app.post("/elders")
def create_elder(elder: ElderCreate):
    """Add a new elder to the system."""
    try:
        new_elder = add_elder(
            name=elder.name,
            phone=elder.phone_number,
            language=elder.language,
            call_time=elder.call_time,
            family_contacts=elder.family_contacts
        )
        return {
            "message": f"Elder '{new_elder.name}' added successfully!",
            "elder_id": new_elder.id,
            "name": new_elder.name,
            "phone": new_elder.phone_number,
            "call_time": new_elder.call_time
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/elders")
def list_elders():
    """Get all elders in the system."""
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
    """Get a specific elder by ID."""
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
    """Twilio calls this when elder picks up."""
    twiml = generate_greeting("Dadi Ji")
    return Response(content=twiml, media_type="text/xml")

@app.post("/call/status")
async def call_status(request: Request):
    """Twilio calls this with call status updates."""
    form_data = await request.form()
    call_status = form_data.get("CallStatus")
    call_sid = form_data.get("CallSid")
    print(f"Call {call_sid} status: {call_status}")
    update_attempt_status(call_sid, call_status)
    return {"status": "received"}

@app.post("/test/call")
async def test_call():
    """Triggers a test call to your verified number."""
    phone = os.getenv("TEST_PHONE_NUMBER")
    if not phone:
        return {"error": "TEST_PHONE_NUMBER not set in .env"}
    call_sid = initiate_call(phone, "Dadi Ji")
    return {
        "message": "Call initiated!",
        "call_sid": call_sid
    }