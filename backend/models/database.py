from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Float, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Phone number as ID
    whatsapp_number = Column(String, unique=True, nullable=False)
    
    # Registration
    verification_code = Column(String, nullable=True)
    verification_code_expires = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    # Security
    pin_hash = Column(String, nullable=True)
    nonce = Column(String, nullable=True)
    
    # Circle Wallet
    circle_wallet_id = Column(String, nullable=True)
    circle_wallet_address = Column(String, nullable=True)
    
    # Status
    registration_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    
    # Transaction details
    transaction_type = Column(String, nullable=False)  # send, receive, split
    amount = Column(Float, nullable=False)
    recipient = Column(String, nullable=True)
    recipient_address = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="pending")  # pending, confirmed, failed
    tx_hash = Column(String, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    
    # Message content
    direction = Column(String, nullable=False)  # inbound, outbound
    message_body = Column(Text, nullable=False)
    message_sid = Column(String, unique=True)
    
    # Context
    intent = Column(String, nullable=True)  # registration, payment, balance, etc.
    workflow_id = Column(String, nullable=True)  # Temporal workflow ID
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()