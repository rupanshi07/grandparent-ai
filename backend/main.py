from fastapi import FastAPI, Request
from fastapi.responses import Response
from dotenv import load_dotenv
from call_handler import initiate_call, generate_greeting
import os

load_dotenv()

app = FastAPI()

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

@app.get("/call/answer")
@app.post("/call/answer")
async def call_answer(request: Request):
    """
    Twilio calls this webhook when elder picks up.
    We return TwiML instructions — what to say.
    """
    twiml = generate_greeting("Dadi Ji")
    return Response(content=twiml, media_type="text/xml")

@app.post("/call/status")
async def call_status(request: Request):
    """
    Twilio calls this webhook with call status updates.
    no-answer, completed, busy, failed etc.
    """
    form_data = await request.form()
    call_status = form_data.get("CallStatus")
    call_sid = form_data.get("CallSid")
    
    print(f"Call {call_sid} status: {call_status}")
    
    return {"status": "received"}

@app.post("/test/call")
async def test_call():
    """
    Test endpoint — triggers a call to your verified number.
    Visit this to make a real call!
    """
    phone = os.getenv("TEST_PHONE_NUMBER")
    if not phone:
        return {"error": "TEST_PHONE_NUMBER not set in .env"}
    
    call_sid = initiate_call(phone, "Dadi Ji")
    return {
        "message": "Call initiated!",
        "call_sid": call_sid
    }