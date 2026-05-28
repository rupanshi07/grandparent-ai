from twilio.rest import Client
from database import get_elder, SessionLocal
from models import Alert
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

def send_missed_call_alert(elder_id: int, call_id: int):
    """
    Called when elder misses all 3 call attempts.
    Sends WhatsApp message to family — NOT a phone call.
    Phone calls are only for emergencies (distress detected).
    """
    elder = get_elder(elder_id)
    if not elder:
        print(f"Elder {elder_id} not found for alert!")
        return

    if not elder.family_contacts:
        print(f"No family contacts for {elder.name}!")
        return

    message = (
        f"🔔 *Grandparent AI Alert*\n\n"
        f"*{elder.name}* did not pick up after 3 call attempts today.\n"
        f"Please check on them when you get a chance.\n\n"
        f"Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n"
        f"_This is an automated message from Grandparent AI_"
    )

    # Send to all family contacts
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    sent_to = []

    for contact in elder.family_contacts:
        phone = contact.get("phone")
        name = contact.get("name", "Family")

        if not phone:
            continue

        try:
            # Send WhatsApp message
            msg = client.messages.create(
                body=message,
                from_=f"whatsapp:{TWILIO_NUMBER}",
                to=f"whatsapp:{phone}"
            )
            sent_to.append(phone)
            print(f"✓ WhatsApp alert sent to {name} ({phone})")

        except Exception as e:
            print(f"WhatsApp failed for {name}, trying SMS...")
            try:
                # Fallback to SMS
                msg = client.messages.create(
                    body=message,
                    from_=TWILIO_NUMBER,
                    to=phone
                )
                sent_to.append(phone)
                print(f"✓ SMS alert sent to {name} ({phone})")
            except Exception as e2:
                print(f"Both failed for {name}: {e2}")

    # Log alert to database
    log_alert(
        elder_id=elder_id,
        call_id=call_id,
        alert_type="missed_calls",
        alert_level="MEDIUM",
        alert_reason="Elder did not pick up after 3 attempts",
        sent_to=",".join(sent_to)
    )

def send_emergency_alert(elder_id: int, call_id: int,
                         reason: str, transcript_excerpt: str):
    """
    Called when distress is detected during a call.
    This is an EMERGENCY — calls family directly!
    If family doesn't pick up, calls next priority contact.
    """
    elder = get_elder(elder_id)
    if not elder:
        return

    if not elder.family_contacts:
        print(f"No family contacts for emergency alert!")
        return

    # Sort by priority
    contacts = sorted(
        elder.family_contacts,
        key=lambda x: x.get("priority", 99)
    )

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    BASE_URL = os.getenv("BASE_URL")

    print(f"EMERGENCY: Calling family for {elder.name}!")

    for contact in contacts:
        phone = contact.get("phone")
        name = contact.get("name", "Family Member")

        if not phone:
            continue

        try:
            # Call family member directly!
            call = client.calls.create(
                to=phone,
                from_=TWILIO_NUMBER,
                twiml=f"""
                <Response>
                    <Say voice="Polly.Aditi" language="hi-IN">
                        Yeh Grandparent AI ka emergency alert hai.
                        {elder.name} ne call mein distress indicate kiya hai.
                        Reason: {reason}.
                        Kripya unhe turant call karein.
                        Yeh ek automated emergency message hai.
                    </Say>
                    <Pause length="2"/>
                    <Say voice="Polly.Aditi" language="hi-IN">
                        Please call {elder.name} immediately.
                        Thank you.
                    </Say>
                </Response>
                """
            )
            print(f"✓ Emergency call made to {name} ({phone})")

            # Log alert
            log_alert(
                elder_id=elder_id,
                call_id=call_id,
                alert_type="distress",
                alert_level="HIGH",
                alert_reason=reason,
                sent_to=phone
            )
            break

        except Exception as e:
            print(f"Emergency call failed for {name}: {e}")
            continue

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
        print(f"✓ Alert logged to database")
    finally:
        db.close()