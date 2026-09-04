from groq import Groq
from dotenv import load_dotenv
import json
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─── LAYER 1: KEYWORD SCANNER ─────────────────────────────────
# These trigger IMMEDIATELY without waiting for LLM
CRITICAL_KEYWORDS = [
    # Physical emergencies
    "chest pain", "seene mein dard", "heart attack",
    "can't breathe", "saans nahi", "sans nahi le pa",
    "fell down", "gir gayi", "gir gaya", "gir gayi hoon",
    "bleeding", "khoon aa raha",
    "unconscious", "behosh",
    "help me", "madad karo", "bachao",
    "ambulance", "hospital jana hai",
    "stroke", "paralysis",
]

HIGH_KEYWORDS = [
    # Health concerns
    "bahut dard", "very pain", "bahut takleef",
    "not eating", "khaana nahi khaya", "bhookh nahi",
    "haven't slept", "neend nahi aayi", "so nahi payi",
    "very dizzy", "chakkar aa rahe", "kamzori",
    "nobody cares", "koi nahi hai", "akela feel",
    "want to die", "jeena nahi", "mar jaana chahti",
    "very lonely", "bahut akela", "bahut akelapan",
    "can't get up", "uth nahi sakti", "uth nahi pa  rahi","sar mein dard", "sir dard", "sar dard",
    "सर दर्द", "सिर दर्द", "सर में दर्द",
    "headache", "head pain",
]

MEDIUM_KEYWORDS = [
    # Emotional distress
    "nobody visits", "koi milne nahi aata",
    "children don't call", "bacche phone nahi karte",
    "feeling sad", "bahut udaas", "rona aa raha",
    "not feeling well", "theek nahi feel",
    "worried", "chinta ho rahi", "darr lag raha",
]

def scan_keywords(text: str) -> dict:
    """
    Layer 1 — Fast keyword scanner.
    Runs in milliseconds — no API call needed.
    Returns distress level based on keywords found.
    """
    text_lower = text.lower()

    # Check CRITICAL keywords first
    for keyword in CRITICAL_KEYWORDS:
        if keyword in text_lower:
            return {
                "level": "CRITICAL",
                "reason": f"Critical keyword detected: '{keyword}'",
                "send_alert": True,
                "call_family": True,
                "keyword_found": keyword
            }

    # Check HIGH keywords
    for keyword in HIGH_KEYWORDS:
        if keyword in text_lower:
            return {
                "level": "HIGH",
                "reason": f"High concern keyword: '{keyword}'",
                "send_alert": True,
                "call_family": False,
                "keyword_found": keyword
            }

    # Check MEDIUM keywords
    for keyword in MEDIUM_KEYWORDS:
        if keyword in text_lower:
            return {
                "level": "MEDIUM",
                "reason": f"Medium concern keyword: '{keyword}'",
                "send_alert": False,
                "call_family": False,
                "keyword_found": keyword
            }

    return {
        "level": "NORMAL",
        "reason": "No distress keywords found",
        "send_alert": False,
        "call_family": False,
        "keyword_found": None
    }

def llm_distress_check(transcript: str) -> dict:
    """
    Layer 2 — LLM distress classifier.
    Called when Layer 1 finds HIGH keywords
    or when we want to verify ambiguous cases.
    More accurate but slower than keyword scan.
    """
    prompt = f"""You are analyzing a phone call transcript with an elderly person.
Determine if there are any signs of physical distress, medical emergency, 
or severe emotional crisis.

TRANSCRIPT:
{transcript}

Respond ONLY with a JSON object like this:
{{
    "distress": true or false,
    "level": "CRITICAL" or "HIGH" or "MEDIUM" or "NORMAL",
    "reason": "brief explanation in one sentence",
    "call_family": true or false
}}

GUIDELINES:
- CRITICAL: Medical emergency, physical danger, suicidal thoughts
- HIGH: Serious health concern, severe emotional distress, not eating/sleeping
- MEDIUM: Mild sadness, loneliness, minor health complaint
- NORMAL: General conversation, minor complaints
- call_family: true only for CRITICAL cases

Respond with JSON only. No other text."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()

        # Clean up response if needed
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)
        result["send_alert"] = result.get("level") in ["CRITICAL", "HIGH"]
        return result

    except Exception as e:
        print(f"LLM distress check error: {e}")
        return {
            "distress": False,
            "level": "NORMAL",
            "reason": "LLM check failed — defaulting to normal",
            "send_alert": False,
            "call_family": False
        }

def detect_distress(text: str, use_llm: bool = False) -> dict:
    """
    Main distress detection function.
    Combines Layer 1 (keywords) and Layer 2 (LLM).

    text: The elder's speech or full transcript
    use_llm: True for full transcript check after call
             False for real-time keyword check during call
    """
    # Always run Layer 1 first — it's instant
    keyword_result = scan_keywords(text)

    # CRITICAL always triggers immediately — no need for LLM
    if keyword_result["level"] == "CRITICAL":
        print(f"CRITICAL distress detected: {keyword_result['reason']}")
        return keyword_result

    # For HIGH keywords — confirm with LLM if requested
    if keyword_result["level"] == "HIGH" and use_llm:
        print(f"HIGH keyword found — confirming with LLM...")
        llm_result = llm_distress_check(text)
        # Take the more severe result
        if llm_result["level"] in ["CRITICAL", "HIGH"]:
            return llm_result
        return keyword_result

    # For full transcript analysis after call — always use LLM
    if use_llm and keyword_result["level"] == "NORMAL":
        return llm_distress_check(text)

    return keyword_result