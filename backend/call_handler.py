from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from fastapi import Request
from dotenv import load_dotenv
import os

load_dotenv()

# Twilio credentials
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
BASE_URL = os.getenv("BASE_URL")

def initiate_call(elder_phone: str, elder_name: str):
    """
    Makes an outbound call to the elder's phone number.
    When they pick up, Twilio fetches instructions from /call/answer
    """
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    call = client.calls.create(
        to=elder_phone,
        from_=TWILIO_NUMBER,
        url=f"{BASE_URL}/call/answer",
        status_callback=f"{BASE_URL}/call/status",
        status_callback_method="POST"
    )

    print(f"Call initiated to {elder_name} - Call SID: {call.sid}")
    return call.sid

def generate_greeting(elder_name: str) -> str:
    """
    Generates TwiML response — instructions Twilio follows during the call.
    This is what the elder hears when they pick up.
    """
    response = VoiceResponse()

    # Greet the elder warmly
    response.say(
        f"Namaskar {elder_name} Ji! Main aapka AI saathi hoon. "
        f"Aap kaisa feel kar rahe hain aaj?",
        voice="Polly.Aditi",  # Indian Hindi voice
        language="hi-IN"
    )

    # Pause and listen for 10 seconds
    response.pause(length=2)

    response.say(
        "I hope you are doing well today. "
        "Your family asked me to check on you. "
        "Please take care and have a wonderful day!",
        voice="Polly.Aditi",
        language="hi-IN"
    )

    return str(response)