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
    """
    Makes an outbound call to the elder.
    When they pick up Twilio fetches /call/answer
    """
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
    """
    First thing elder hears when they pick up.
    Uses Gather to listen for their response.
    Longer timeout so elder has time to speak fully.
    """
    response = VoiceResponse()

    # Greet warmly
    response.say(
        f"Namaskar {elder_name} Ji! "
        f"Main aapka AI saathi bol raha hoon. "
        f"Aap kaisa feel kar rahe hain aaj?",
        voice="Polly.Aditi",
        language="hi-IN"
    )

    # Listen for elder's response
    # timeout=8 gives elder 8 seconds to start speaking
    # speech_timeout=3 waits 3 seconds of silence before cutting off
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/call/respond/{elder_id}",
        method="POST",
        timeout=8,
        speech_timeout="3",
        language="hi-IN"
    )
    response.append(gather)

    # If elder doesn't speak at all — try again
    response.redirect(f"{BASE_URL}/call/answer")

    return str(response)

def generate_response(elder_name: str, elder_id: int,
                      ai_reply: str) -> str:
    """
    Speaks the AI reply and listens for elder's next response.
    This creates the back-and-forth conversation loop.
    """
    response = VoiceResponse()

    # Speak the AI reply
    response.say(
        ai_reply,
        voice="Polly.Aditi",
        language="hi-IN"
    )

    # Listen for elder's response
    # Same generous timeout as greeting
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/call/respond/{elder_id}",
        method="POST",
        timeout=8,
        speech_timeout="3",
        language="hi-IN"
    )
    response.append(gather)

    # If elder doesn't speak — end call warmly
    response.say(
        "Apna khayal rakhiye Dadi Ji. "
        "Aapka parivaar aapko bahut pyaar karta hai. Namaste!",
        voice="Polly.Aditi",
        language="hi-IN"
    )
    response.hangup()

    return str(response)

def generate_goodbye(elder_name: str) -> str:
    """
    Warm goodbye message to end the call.
    """
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