from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Elder(Base):
    """
    Stores information about each elderly person.
    One row per elder registered in the system.
    """
    __tablename__ = "elders"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, nullable=False)
    phone_number    = Column(String, unique=True, nullable=False)
    language        = Column(String, default="hindi")
    call_time       = Column(String, default="09:00")
    memory_summary  = Column(Text, default="")
    family_contacts = Column(JSON, default=list)
    created_at      = Column(DateTime, default=datetime.utcnow)

class Call(Base):
    """
    Stores one row per call session.
    A session = one scheduled daily call (may have up to 3 attempts).
    """
    __tablename__ = "calls"

    id               = Column(Integer, primary_key=True, index=True)
    elder_id         = Column(Integer, nullable=False)
    started_at       = Column(DateTime, default=datetime.utcnow)
    ended_at         = Column(DateTime, nullable=True)
    full_transcript  = Column(Text, default="")
    call_summary     = Column(Text, default="")
    distress_level   = Column(String, default="NORMAL")
    attempt_count    = Column(Integer, default=0)

class CallAttempt(Base):
    """
    Stores each individual ring attempt.
    One Call can have up to 3 CallAttempts.
    This is what powers your retry logic!
    """
    __tablename__ = "call_attempts"

    id             = Column(Integer, primary_key=True, index=True)
    call_id        = Column(Integer, nullable=False)
    elder_id       = Column(Integer, nullable=False)
    attempt_number = Column(Integer, nullable=False)
    twilio_call_sid= Column(String, nullable=True)
    status         = Column(String, default="initiated")
    tried_at       = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    """
    Stores every alert sent to family members.
    Both WhatsApp alerts and emergency phone calls.
    """
    __tablename__ = "alerts"

    id           = Column(Integer, primary_key=True, index=True)
    call_id      = Column(Integer, nullable=True)
    elder_id     = Column(Integer, nullable=False)
    alert_type   = Column(String, nullable=False)
    alert_level  = Column(String, nullable=False)
    alert_reason = Column(Text, default="")
    sent_to      = Column(String, default="")
    sent_at      = Column(DateTime, default=datetime.utcnow)