from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv
import os

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
BASE_URL = os.getenv("BASE_URL")

def initiate_call(elder_phone: str, elder_name: str):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    call = client.calls.create(
        to=elder_phone,
        from_=TWILIO_NUMBER,
        url=f"{BASE_URL}/call/answer",
        status_callback=f"{BASE_URL}/call/status",
        status_callback_method="POST"
    )
    print(f"Call initiated to {elder_name} - SID: {call.sid}")
    return call.sid

def generate_greeting(elder_name: str, elder_id: int) -> str:
    response = VoiceResponse()
    response.say(
        f"Namaskar {elder_name} Ji! "
        f"Main aapka AI saathi bol raha hoon. "
        f"Aap kaisa feel kar rahe hain aaj?",
        voice="Polly.Aditi",
        language="hi-IN"
    )
    response.pause(length=1)
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/call/respond/{elder_id}",
        method="POST",
        timeout=15,
        speech_timeout="auto",
        language="hi-IN"
    )
    response.append(gather)
    response.redirect(f"{BASE_URL}/call/answer")
    return str(response)

def generate_response(elder_name: str, elder_id: int, ai_reply: str) -> str:
    response = VoiceResponse()
    response.say(
        ai_reply,
        voice="Polly.Aditi",
        language="hi-IN"
    )
    response.pause(length=1)
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/call/respond/{elder_id}",
        method="POST",
        timeout=15,
        speech_timeout="auto",
        language="hi-IN"
    )
    response.append(gather)
    response.say(
        "Apna khayal rakhiye Dadi Ji. "
        "Aapka parivaar aapko bahut pyaar karta hai. Namaste!",
        voice="Polly.Aditi",
        language="hi-IN"
    )
    response.hangup()
    return str(response)

def generate_goodbye(elder_name: str) -> str:
    response = VoiceResponse()
    response.say(
        f"Bahut accha laga aapse baat karke {elder_name} Ji. "
        f"Apna khayal rakhiye. "
        f"Aapka poora parivaar aapko bahut pyaar karta hai. "
        f"Namaste!",
        voice="Polly.Aditi",
        language="hi-IN"
    )
    response.hangup()
    return str(response)