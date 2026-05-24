from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Grandparent AI server is running!"}

@app.get("/")
def home():
    return {
        "project": "Grandparent AI Companion",
        "version": "1.0",
        "status": "running"
    }

@app.get("/check-keys")
def check_keys():
    return {
        "twilio": "✓ loaded" if os.getenv("TWILIO_ACCOUNT_SID") else "✗ missing",
        "anthropic": "✓ loaded" if os.getenv("ANTHROPIC_API_KEY") else "✗ missing",
        "elevenlabs": "✓ loaded" if os.getenv("ELEVENLABS_API_KEY") else "✗ missing",
    }