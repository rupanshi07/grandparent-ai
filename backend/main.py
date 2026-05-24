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