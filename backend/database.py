from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grandparent.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create database engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Creates all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")

def get_db():
    """
    Returns a database session.
    Always close the session after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_elder(user_id: int, name: str, phone: str, language: str,
              call_time: str, family_contacts: list):
    """Adds a new elder to the database, linked to the owning user."""
    from models import Elder
    db = SessionLocal()
    try:
        elder = Elder(
            user_id=user_id,
            name=name,
            phone_number=phone,
            language=language,
            call_time=call_time,
            family_contacts=family_contacts,
            memory_summary=f"This is {name}. No previous calls yet."
        )
        db.add(elder)
        db.commit()
        db.refresh(elder)
        print(f"✓ Elder '{name}' added with ID: {elder.id} for user {user_id}")
        return elder
    finally:
        db.close()

def get_elder(elder_id: int):
    """Gets an elder by their ID."""
    from models import Elder
    db = SessionLocal()
    try:
        return db.query(Elder).filter(Elder.id == elder_id).first()
    finally:
        db.close()

def get_all_elders(user_id: int = None):
    """
    Gets elders from the database.
    If user_id is given, only returns elders belonging to that user.
    If user_id is None, returns all elders (used by the scheduler internally).
    """
    from models import Elder
    db = SessionLocal()
    try:
        query = db.query(Elder)
        if user_id is not None:
            query = query.filter(Elder.user_id == user_id)
        return query.all()
    finally:
        db.close()

def log_call_attempt(elder_id: int, call_id: int,
                     attempt_number: int, twilio_sid: str):
    """Logs each call attempt to the database."""
    from models import CallAttempt
    db = SessionLocal()
    try:
        attempt = CallAttempt(
            elder_id=elder_id,
            call_id=call_id,
            attempt_number=attempt_number,
            twilio_call_sid=twilio_sid,
            status="initiated"
        )
        db.add(attempt)
        db.commit()
        print(f"✓ Attempt {attempt_number} logged for elder {elder_id}")
        return attempt
    finally:
        db.close()

def update_attempt_status(twilio_sid: str, status: str):
    """Updates a call attempt status when Twilio sends callback."""
    from models import CallAttempt
    db = SessionLocal()
    try:
        attempt = db.query(CallAttempt).filter(
            CallAttempt.twilio_call_sid == twilio_sid
        ).first()
        if attempt:
            attempt.status = status
            db.commit()
            print(f"✓ Attempt {twilio_sid} status updated to: {status}")
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()