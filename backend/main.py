from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
from auth import (hash_password, verify_password, create_access_token,
                  get_current_user_id)
from pydantic import BaseModel
from dotenv import load_dotenv
from call_handler import (initiate_call, generate_greeting,
                          generate_response, generate_goodbye)
from conversation import get_ai_response
from database import (create_tables, add_elder, get_elder,
                      get_all_elders, update_attempt_status,
                      SessionLocal)
import os
import threading
import atexit

load_dotenv()
create_tables()

# Start scheduler
from scheduler import start_scheduler, stop_scheduler
start_scheduler()
atexit.register(stop_scheduler)

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

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

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

# ─── AUTH ENDPOINTS ────────────────────────────────────────────
@app.post("/auth/signup")
def signup(data: SignupRequest):
    """Creates a new family account."""
    from models import User
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(new_user.id, new_user.email)
        return {
            "message": "Account created successfully!",
            "token": token,
            "user": {"id": new_user.id, "email": new_user.email, "full_name": new_user.full_name}
        }
    finally:
        db.close()

@app.post("/auth/login")
def login(data: LoginRequest):
    """Logs in an existing user with email + password."""
    from models import User
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == data.email).first()
        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(user.id, user.email)
        return {
            "message": "Login successful!",
            "token": token,
            "user": {"id": user.id, "email": user.email, "full_name": user.full_name}
        }
    finally:
        db.close()

@app.get("/auth/me")
def get_me(user_id: int = Depends(get_current_user_id)):
    """Returns the currently logged-in user's info. Used to verify the token works."""
    from models import User
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "email": user.email, "full_name": user.full_name}
    finally:
        db.close()

# ─── ELDER ENDPOINTS ──────────────────────────────────────────
@app.post("/elders")
def create_elder(elder: ElderCreate, user_id: int = Depends(get_current_user_id)):
    try:
        new_elder = add_elder(
            user_id=user_id,
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
def list_elders(user_id: int = Depends(get_current_user_id)):
    elders = get_all_elders(user_id=user_id)
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
def get_elder_by_id(elder_id: int, user_id: int = Depends(get_current_user_id)):
    elder = get_elder(elder_id)
    if not elder or elder.user_id != user_id:
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
    Only initialise conversation if fresh call.
    """
    elder_id = 1
    elder = get_elder(elder_id)
    elder_name = elder.name if elder else "Dadi Ji"

    if elder_id not in active_conversations:
        active_conversations[elder_id] = []

    twiml = generate_greeting(elder_name, elder_id)
    return Response(content=twiml, media_type="text/xml")

@app.post("/call/respond/{elder_id}")
async def call_respond(elder_id: int, request: Request):
    """
    Twilio sends us what the elder said.
    We check for distress, get AI response and speak it back.
    This is the CONVERSATION LOOP!
    """
    from distress import detect_distress
    from alerts import send_emergency_alert
    from memory import build_transcript

    form_data = await request.form()
    elder_speech = form_data.get("SpeechResult", "")
    confidence = form_data.get("Confidence", "0")

    print(f"Elder said: '{elder_speech}' (confidence: {confidence})")

    if not elder_speech or len(elder_speech.strip()) < 2:
        response = VoiceResponse()
        response.say(
            "Mujhe sunai nahi diya. Kya aap dobara bol sakte hain?",
            voice="Polly.Aditi",
            language="hi-IN"
        )
        gather = Gather(
            input="speech",
            action=f"{os.getenv('BASE_URL')}/call/respond/{elder_id}",
            method="POST",
            timeout=8,
            speech_timeout="3",
            language="hi-IN"
        )
        response.append(gather)
        response.hangup()
        return Response(content=str(response), media_type="text/xml")

    elder = get_elder(elder_id)
    if not elder:
        return Response(
            content=generate_goodbye("Dadi Ji"),
            media_type="text/xml"
        )

    if elder_id not in active_conversations:
        active_conversations[elder_id] = []

    history = active_conversations[elder_id]

    # ─── DISTRESS DETECTION ───────────────────────────────
    distress_result = detect_distress(elder_speech, use_llm=False)
    print(f"Distress check: {distress_result['level']}")

    if distress_result["level"] == "CRITICAL":
        print("CRITICAL distress! Calling family immediately!")
        from scheduler import active_call_sessions
        call_id = active_call_sessions.get(elder_id, 0)
        threading.Thread(
            target=send_emergency_alert,
            args=(elder_id, call_id,
                  distress_result["reason"], elder_speech)
        ).start()

    elif distress_result["level"] == "HIGH":
        print("HIGH distress detected — monitoring closely")

    # ─── CHECK IF ELDER WANTS TO END CALL ─────────────────
    end_phrases = ["bye", "goodbye", "alvida", "band karo",
                   "rakhna", "theek hai bas", "bas karo"]
    if any(phrase in elder_speech.lower() for phrase in end_phrases):
        twiml = generate_goodbye(elder.name)
        active_conversations.pop(elder_id, None)
        return Response(content=twiml, media_type="text/xml")

    if len(history) >= 16:
        twiml = generate_goodbye(elder.name)
        active_conversations.pop(elder_id, None)
        return Response(content=twiml, media_type="text/xml")

    # ─── GET AI RESPONSE ──────────────────────────────────
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
    """
    Twilio sends call status updates here.
    Handles 3 scenarios:
    1. completed — save memory + full distress scan
    2. no-answer — trigger retry logic
    3. busy/failed — treat as no-answer
    """
    from memory import update_memory, build_transcript
    from scheduler import (handle_no_answer, handle_call_answered,
                           active_call_sessions)

    form_data = await request.form()
    status = form_data.get("CallStatus")
    sid = form_data.get("CallSid")

    print(f"Call {sid} status: {status}")
    update_attempt_status(sid, status)

    db = SessionLocal()
    try:
        from models import CallAttempt
        attempt = db.query(CallAttempt).filter(
            CallAttempt.twilio_call_sid == sid
        ).first()

        if not attempt:
            print(f"No attempt found for SID {sid}")
            if status == "completed":
                elder_id = 1
                if elder_id in active_conversations:
                    history = active_conversations[elder_id]
                    if len(history) > 0:
                        transcript = build_transcript(history)
                        threading.Thread(
                            target=update_memory,
                            args=(elder_id, transcript)
                        ).start()
                    active_conversations.pop(elder_id, None)
            return {"status": "received"}

        elder_id = attempt.elder_id
        call_id = attempt.call_id
        attempt_number = attempt.attempt_number

    finally:
        db.close()

    if status == "completed":
        print(f"Call completed for elder {elder_id}")
        handle_call_answered(elder_id)

        if elder_id in active_conversations:
            history = active_conversations[elder_id]
            if len(history) > 0:
                transcript = build_transcript(history)
                print("Saving memory + running distress scan...")

                def save_and_scan(eid, trans, cid):
                    update_memory(eid, trans)
                    from distress import detect_distress
                    full_result = detect_distress(trans, use_llm=True)
                    print(f"Full distress scan: {full_result['level']}")
                    db2 = SessionLocal()
                    try:
                        from models import Call
                        call = db2.query(Call).filter(
                            Call.id == cid
                        ).first()
                        if call:
                            call.distress_level = full_result["level"]
                            db2.commit()
                            print(f"✓ Distress level saved: {full_result['level']}")
                    finally:
                        db2.close()
                    if full_result["send_alert"]:
                        from alerts import send_emergency_alert
                        send_emergency_alert(
                            eid, cid,
                            full_result["reason"], trans
                        )

                threading.Thread(
                    target=save_and_scan,
                    args=(elder_id, transcript, call_id)
                ).start()

            active_conversations.pop(elder_id, None)

        active_call_sessions.pop(elder_id, None)

    elif status in ["no-answer", "busy", "failed"]:
        print(f"No answer on attempt {attempt_number} for elder {elder_id}")
        handle_no_answer(elder_id, call_id, attempt_number)

    return {"status": "received"}

@app.post("/test/call")
async def test_call():
    """Triggers a test call."""
    phone = os.getenv("TEST_PHONE_NUMBER")
    if not phone:
        return {"error": "TEST_PHONE_NUMBER not set in .env"}
    call_sid = initiate_call(phone, "Dadi Ji")
    return {"message": "Call initiated!", "call_sid": call_sid}

@app.post("/test/retry")
async def test_retry():
    """Tests the retry logic."""
    from scheduler import initiate_call_session
    threading.Thread(
        target=initiate_call_session,
        args=[1]
    ).start()
    return {"message": "Retry test started! Watch server logs."}

@app.post("/test/distress")
async def test_distress():
    """Tests distress detection."""
    from distress import detect_distress
    test_phrases = [
        "Main theek hoon aaj",
        "Bahut dard ho raha hai",
        "Seene mein dard ho raha hai bachao"
    ]
    results = []
    for phrase in test_phrases:
        result = detect_distress(phrase)
        results.append({
            "phrase": phrase,
            "level": result["level"],
            "reason": result["reason"]
        })
    return {"distress_tests": results}

@app.get("/elders/{elder_id}/alerts")
def get_elder_alerts(elder_id: int, user_id: int = Depends(get_current_user_id)):
    """Gets all alerts for an elder — used by dashboard."""
    from alerts import get_alerts_for_elder
    elder = get_elder(elder_id)
    if not elder or elder.user_id != user_id:
        raise HTTPException(status_code=404, detail="Elder not found")
    alerts = get_alerts_for_elder(elder_id)
    return {
        "elder_name": elder.name,
        "total_alerts": len(alerts),
        "alerts": alerts
    }

@app.post("/alerts/call-status")
async def alert_call_status(request: Request):
    """
    Twilio calls this when emergency family call
    status changes. Tracks if family picked up.
    """
    form_data = await request.form()
    status = form_data.get("CallStatus")
    sid = form_data.get("CallSid")
    print(f"Emergency alert call {sid} status: {status}")
    return {"status": "received"}

@app.post("/test/alert")
async def test_alert():
    """
    Tests the missed call alert system.
    Sends WhatsApp/SMS to family contacts of elder 1.
    """
    from alerts import send_missed_call_alert
    threading.Thread(
        target=send_missed_call_alert,
        args=(1, 0)
    ).start()
    return {"message": "Alert test triggered! Check family WhatsApp/SMS."}

@app.patch("/elders/{elder_id}/schedule")
def update_schedule(elder_id: int, data: dict, user_id: int = Depends(get_current_user_id)):
    """Updates elder's call schedule."""
    from scheduler import schedule_elder_daily_call
    db = SessionLocal()
    try:
        from models import Elder
        elder = db.query(Elder).filter(Elder.id == elder_id).first()
        if not elder or elder.user_id != user_id:
            raise HTTPException(status_code=404, detail="Elder not found")
        elder.call_time = data.get("call_time", elder.call_time)
        db.commit()
        schedule_elder_daily_call(elder_id, elder.call_time)
        return {"message": f"Schedule updated to {elder.call_time}"}
    finally:
        db.close()

@app.delete("/elders/{elder_id}")
def delete_elder(elder_id: int, user_id: int = Depends(get_current_user_id)):
    """Deletes an elder from the system."""
    db = SessionLocal()
    try:
        from models import Elder
        elder = db.query(Elder).filter(Elder.id == elder_id).first()
        if not elder or elder.user_id != user_id:
            raise HTTPException(status_code=404, detail="Elder not found")
        db.delete(elder)
        db.commit()
        return {"message": f"Elder {elder_id} deleted"}
    finally:
        db.close()

@app.post("/admin/migrate")
def run_migration():
    """
    ONE-TIME USE: drops and recreates all tables to apply schema changes.
    Remove this endpoint after running it once.
    """
    from models import Base
    from database import engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"message": "Migration complete — all tables recreated with new schema"}