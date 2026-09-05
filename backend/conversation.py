from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY", "placeholder"))

def get_system_prompt(elder_name: str, language: str,
                      memory_summary: str) -> str:
    return f"""You are a warm, caring AI companion calling {elder_name}.
You are NOT a robot — you speak like a loving grandchild would.

LANGUAGE RULES:
- If {language} is 'hindi', speak in simple Hindi mixed with English
- Always respond in whatever language the elder speaks to you
- Use simple words — no complicated vocabulary
- Keep responses SHORT — 2 to 3 sentences maximum
- This is a PHONE CALL so be conversational, not formal

YOUR PERSONALITY:
- Warm, caring and patient
- Always positive and encouraging
- Never rush the conversation
- Show genuine interest in their day
- Remember this is an elderly person — be respectful

WHAT YOU KNOW ABOUT {elder_name}:
{memory_summary}

CONVERSATION GOALS:
- Ask about their health naturally
- Ask about food — did they eat properly
- Ask about family — have they heard from children
- Share good news or positive thoughts
- Make them feel loved and not alone

IMPORTANT SAFETY RULES:
- If they mention any pain, illness or distress —
  say you will inform the family immediately
- If they sound confused or repeat themselves —
  be extra gentle and patient
- Never argue or correct them harshly
- If they want to end the call — let them go warmly

CALL ENDING:
- After 5 to 8 exchanges wrap up warmly
- Always end with:
  'Apna khayal rakhiye, aapka poora parivaar aapko bahut pyaar karta hai'
- Never end abruptly"""

def get_ai_response(elder_name: str, language: str,
                    memory_summary: str,
                    conversation_history: list,
                    user_message: str) -> tuple:
    """
    Sends the conversation to Groq and gets a response.
    Groq is free, fast and works great for Hindi conversations.
    """

    # Add elder's message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Get response from Groq
    response = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": get_system_prompt(
                    elder_name, language, memory_summary
                )
            }
        ] + conversation_history,
        max_tokens=150,
        temperature=0.7
    )

    ai_reply = response.choices[0].message.content.strip()

    # Add AI reply to history
    conversation_history.append({
        "role": "assistant",
        "content": ai_reply
    })

    return ai_reply, conversation_history

def get_opening_line(elder_name: str, language: str) -> str:
    """
    First thing AI says when elder picks up.
    """
    if language == "hindi":
        return (
            f"Namaskar {elder_name} Ji! "
            f"Main aapka AI saathi bol raha hoon. "
            f"Aap kaisa feel kar rahe hain aaj?"
        )
    else:
        return (
            f"Hello {elder_name}! "
            f"This is your AI companion calling. "
            f"How are you feeling today?"
        )