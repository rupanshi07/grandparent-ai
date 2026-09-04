from groq import Groq
from database import SessionLocal
from models import Elder
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_memory(elder_id: int) -> str:
    """
    Reads the current memory summary for an elder.
    This gets injected into every call's system prompt.
    """
    db = SessionLocal()
    try:
        elder = db.query(Elder).filter(Elder.id == elder_id).first()
        if elder and elder.memory_summary:
            return elder.memory_summary
        return "No previous calls yet."
    finally:
        db.close()

def update_memory(elder_id: int, transcript: str) -> str:
    """
    After every call, this function:
    1. Takes the old memory summary
    2. Adds today's conversation transcript
    3. Asks Groq to write a new compressed summary
    4. Saves it to the database
    
    This way the AI always knows what was discussed before!
    """
    db = SessionLocal()
    try:
        elder = db.query(Elder).filter(Elder.id == elder_id).first()
        if not elder:
            return "Elder not found"

        old_summary = elder.memory_summary or "No previous calls."

        # Ask Groq to create updated memory summary
        prompt = f"""You are helping maintain a memory summary of an elderly person 
for an AI companion that calls them daily.

OLD MEMORY SUMMARY:
{old_summary}

TODAY'S CALL TRANSCRIPT:
{transcript}

Write an updated memory summary in exactly 150 words covering:
- Health status and any complaints mentioned
- Mood and emotional state  
- Family members mentioned or missed
- Topics of interest (food, news, religion, grandchildren)
- Any concerning statements made
- What they did today

Write naturally as if describing the person to a caring family member.
Do NOT use bullet points — write in flowing sentences.
Maximum 150 words."""

        response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.5
        )

        new_summary = response.choices[0].message.content.strip()

        # Save to database
        elder.memory_summary = new_summary
        db.commit()

        print(f"✓ Memory updated for {elder.name}")
        print(f"New summary: {new_summary[:100]}...")

        return new_summary

    finally:
        db.close()

def build_transcript(conversation_history: list) -> str:
    """
    Converts conversation history list into readable transcript text.
    """
    transcript = ""
    for msg in conversation_history:
        role = "Elder" if msg["role"] == "user" else "AI Companion"
        transcript += f"{role}: {msg['content']}\n"
    return transcript