from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from database import (SessionLocal, get_all_elders,
                      get_elder, log_call_attempt)
from models import Call, CallAttempt
from dotenv import load_dotenv
import pytz
import os

load_dotenv()

# India timezone
IST = pytz.timezone("Asia/Kolkata")

# Create scheduler with IST timezone
scheduler = BackgroundScheduler(timezone=IST)

# Track active call sessions
# Key: elder_id, Value: call_id
active_call_sessions = {}

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("✓ Scheduler started!")
        schedule_all_elders()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped.")

def schedule_all_elders():
    elders = get_all_elders()
    for elder in elders:
        schedule_elder_daily_call(elder.id, elder.call_time)
    print(f"✓ Scheduled calls for {len(elders)} elders")

def schedule_elder_daily_call(elder_id: int, call_time: str):
    job_id = f"daily_call_elder_{elder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    hour, minute = map(int, call_time.split(":"))
    scheduler.add_job(
        func=initiate_call_session,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        args=[elder_id],
        replace_existing=True
    )
    print(f"✓ Daily call scheduled for elder {elder_id} at {call_time}")

def initiate_call_session(elder_id: int):
    from call_handler import initiate_call
    elder = get_elder(elder_id)
    if not elder:
        print(f"Elder {elder_id} not found!")
        return
    if elder_id in active_call_sessions:
        print(f"Call already active for elder {elder_id}")
        return
    db = SessionLocal()
    try:
        call = Call(
            elder_id=elder_id,
            started_at=datetime.now(IST),
            attempt_count=0
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        call_id = call.id
    finally:
        db.close()
    active_call_sessions[elder_id] = call_id
    print(f"Starting call session {call_id} for {elder.name}")
    make_call_attempt(elder_id, call_id, attempt_number=1)

def make_call_attempt(elder_id: int, call_id: int,
                      attempt_number: int):
    from call_handler import initiate_call
    elder = get_elder(elder_id)
    if not elder:
        return
    print(f"Making attempt {attempt_number} for {elder.name}")
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.attempt_count = attempt_number
            db.commit()
    finally:
        db.close()
    try:
        call_sid = initiate_call(elder.phone_number, elder.name)
        log_call_attempt(
            elder_id=elder_id,
            call_id=call_id,
            attempt_number=attempt_number,
            twilio_sid=call_sid
        )
        print(f"✓ Attempt {attempt_number} initiated - SID: {call_sid}")
    except Exception as e:
        print(f"Error making call attempt: {e}")

def handle_no_answer(elder_id: int, call_id: int,
                     attempt_number: int):
    """
    YOUR retry logic:
    Attempt 1 failed → wait 3 min → attempt 2
    Attempt 2 failed → wait 10 min → attempt 3
    Attempt 3 failed → alert family
    """
    print(f"No answer on attempt {attempt_number} for elder {elder_id}")

    if attempt_number == 1:
        retry_time = datetime.now(IST) + timedelta(minutes=3)
        scheduler.add_job(
            func=make_call_attempt,
            trigger=DateTrigger(run_date=retry_time),
            args=[elder_id, call_id, 2],
            id=f"retry_2_elder_{elder_id}",
            replace_existing=True
        )
        print(f"Attempt 2 scheduled in 3 minutes for elder {elder_id}")

    elif attempt_number == 2:
        retry_time = datetime.now(IST) + timedelta(minutes=10)
        scheduler.add_job(
            func=make_call_attempt,
            trigger=DateTrigger(run_date=retry_time),
            args=[elder_id, call_id, 3],
            id=f"retry_3_elder_{elder_id}",
            replace_existing=True
        )
        print(f"Attempt 3 scheduled in 10 minutes for elder {elder_id}")

    elif attempt_number == 3:
        print(f"All 3 attempts failed for elder {elder_id} — alerting family!")
        active_call_sessions.pop(elder_id, None)
        from alerts import send_missed_call_alert
        send_missed_call_alert(elder_id, call_id)

def handle_call_answered(elder_id: int):
    for attempt in [2, 3]:
        job_id = f"retry_{attempt}_elder_{elder_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            print(f"Cancelled retry job {job_id}")