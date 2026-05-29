from twilio.rest import Client
from database import get_elder, SessionLocal
from models import Alert
from datetime import datetime
from dotenv import load_dotenv
import time
import os

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
BASE_URL = os.getenv("BASE_URL")

def send_whatsapp_message(to_phone: str, message: str) -> bool:
    """
    Sends a WhatsApp message to a phone number.
    Returns True if successful, False if failed.
    """
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=f"whatsapp:{TWILIO_NUMBER}",
            to=f"whatsapp:{to_phone}"
        )
        print(f"✓ WhatsApp sent to {to_phone}")
        return True
    except Exception as e:
        print(f"WhatsApp failed for {to_phone}: {e}")
        return False

def send_sms_message(to_phone: str, message: str) -> bool:
    """
    Sends an SMS to a phone number.
    Fallback when WhatsApp fails.
    Returns True if successful, False if failed.
    """
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=to_phone
        )
        print(f"✓ SMS sent to {to_phone}")
        return True
    except Exception as e:
        print(f"SMS failed for {to_phone}: {e}")
        return False

def send_missed_call_alert(elder_id: int, call_id: int):
    """
    Called when elder misses ALL 3 call attempts.
    This is a NORMAL alert — not an emergency.
    Sends WhatsApp to all family members.
    Does NOT call anyone — just a message.
    """
    elder = get_elder(elder_id)
    if not elder:
        print(f"Elder {elder_id} not found!")
        return

    if not elder.family_contacts:
        print(f"No family contacts for {elder.name}!")
        return

    message = (
        f"🔔 *Grandparent AI — Missed Call Alert*\n\n"
        f"*{elder.name}* did not pick up after 3 call attempts today.\n\n"
        f"Please check on them when you get a chance.\n\n"
        f"📅 Date: {datetime.now().strftime('%d %b %Y')}\n"
        f"⏰ Time: {datetime.now().strftime('%I:%M %p')}\n\n"
        f"_Automated message from Grandparent AI_"
    )

    sent_to = []
    for contact in elder.family_contacts:
        phone = contact.get("phone")
        name = contact.get("name", "Family")

        if not phone:
            continue

        # Try WhatsApp first
        success = send_whatsapp_message(phone, message)

        # Fallback to SMS if WhatsApp fails
        if not success:
            success = send_sms_message(phone, message)

        if success:
            sent_to.append(phone)
            print(f"✓ Missed call alert sent to {name}")

    # Log to database
    log_alert(
        elder_id=elder_id,
        call_id=call_id,
        alert_type="missed_calls",
        alert_level="MEDIUM",
        alert_reason=f"{elder.name} did not pick up after 3 attempts",
        sent_to=",".join(sent_to)
    )

    print(f"✓ Missed call alerts sent to {len(sent_to)} contacts")

def send_emergency_alert(elder_id: int, call_id: int,
                         reason: str, transcript_excerpt: str):
    """
    Called when CRITICAL or HIGH distress detected.
    This IS an emergency — calls family directly!

    YOUR escalation logic:
    1. Call family member priority 1
    2. If no answer → call priority 2
    3. If no answer → call priority 3
    4. If nobody picks up → SMS all family members
    """
    elder = get_elder(elder_id)
    if not elder:
        print(f"Elder {elder_id} not found!")
        return

    if not elder.family_contacts:
        print(f"No family contacts for emergency!")
        return

    # Sort contacts by priority
    contacts = sorted(
        elder.family_contacts,
        key=lambda x: x.get("priority", 99)
    )

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    someone_answered = False

    print(f"🚨 EMERGENCY: Starting escalation for {elder.name}")
    print(f"Reason: {reason}")

    for i, contact in enumerate(contacts):
        phone = contact.get("phone")
        name = contact.get("name", "Family Member")

        if not phone:
            continue

        print(f"Calling {name} ({phone}) — priority {i+1}")

        try:
            # Call family member with emergency voice message
            call = client.calls.create(
                to=phone,
                from_=TWILIO_NUMBER,
                twiml=f"""
                <Response>
                    <Say voice="Polly.Aditi" language="hi-IN">
                        Namaste. Yeh Grandparent AI ka emergency alert hai.
                        {elder.name} ne call mein distress indicate kiya hai.
                        Wajah: {reason}.
                        Kripya unhe turant call karein ya unke paas jaayein.
                        Yeh ek automated emergency message hai.
                    </Say>
                    <Pause length="1"/>
                    <Say voice="Polly.Aditi" language="hi-IN">
                        Please check on {elder.name} immediately.
                        Thank you.
                    </Say>
                </Response>
                """,
                status_callback=f"{BASE_URL}/alerts/call-status",
                status_callback_method="POST"
            )

            print(f"✓ Emergency call made to {name} - SID: {call.sid}")

            # Wait 45 seconds to see if they pick up
            print(f"Waiting 45 seconds for {name} to answer...")
            time.sleep(45)

            # Check call status
            call_details = client.calls(call.sid).fetch()
            if call_details.status == "completed":
                print(f"✓ {name} picked up the emergency call!")
                someone_answered = True

                # Log successful alert
                log_alert(
                    elder_id=elder_id,
                    call_id=call_id,
                    alert_type="distress",
                    alert_level="CRITICAL",
                    alert_reason=reason,
                    sent_to=phone
                )
                break
            else:
                print(f"{name} did not answer — trying next contact...")

        except Exception as e:
            print(f"Emergency call failed for {name}: {e}")
            continue

    # If nobody answered — send SMS to ALL family members
    if not someone_answered:
        print("Nobody answered emergency calls — sending SMS to all!")
        sms_message = (
            f"🚨 EMERGENCY ALERT — Grandparent AI\n\n"
            f"{elder.name} needs immediate attention!\n\n"
            f"Reason: {reason}\n\n"
            f"What was said: {transcript_excerpt[:100]}...\n\n"
            f"Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"PLEASE CHECK ON THEM IMMEDIATELY!"
        )

        all_sent_to = []
        for contact in contacts:
            phone = contact.get("phone")
            name = contact.get("name", "Family")
            if phone:
                success = send_sms_message(phone, sms_message)
                if success:
                    all_sent_to.append(phone)

        log_alert(
            elder_id=elder_id,
            call_id=call_id,
            alert_type="distress_sms_fallback",
            alert_level="CRITICAL",
            alert_reason=f"Nobody answered emergency calls. {reason}",
            sent_to=",".join(all_sent_to)
        )

        print(f"✓ Emergency SMS sent to {len(all_sent_to)} contacts")

def send_dashboard_notification(elder_id: int, call_id: int,
                                level: str, message: str):
    """
    Updates the dashboard with a notification.
    This is stored in DB and shown on family dashboard.
    """
    log_alert(
        elder_id=elder_id,
        call_id=call_id,
        alert_type="dashboard",
        alert_level=level,
        alert_reason=message,
        sent_to="dashboard"
    )
    print(f"✓ Dashboard notification logged: {message}")

def log_alert(elder_id: int, call_id: int, alert_type: str,
              alert_level: str, alert_reason: str, sent_to: str):
    """Saves alert record to database."""
    db = SessionLocal()
    try:
        alert = Alert(
            elder_id=elder_id,
            call_id=call_id,
            alert_type=alert_type,
            alert_level=alert_level,
            alert_reason=alert_reason,
            sent_to=sent_to,
            sent_at=datetime.utcnow()
        )
        db.add(alert)
        db.commit()
        print(f"✓ Alert logged: {alert_type} — {alert_level}")
    except Exception as e:
        print(f"Alert logging error: {e}")
    finally:
        db.close()

def get_alerts_for_elder(elder_id: int) -> list:
    """Gets all alerts for an elder — used by dashboard."""
    db = SessionLocal()
    try:
        alerts = db.query(Alert).filter(
            Alert.elder_id == elder_id
        ).order_by(Alert.sent_at.desc()).all()

        return [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "alert_level": a.alert_level,
                "alert_reason": a.alert_reason,
                "sent_to": a.sent_to,
                "sent_at": str(a.sent_at)
            }
            for a in alerts
        ]
    finally:
        db.close()