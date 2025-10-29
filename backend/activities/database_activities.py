from temporalio import activity
from models.database import User, Transaction, Message, SessionLocal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import secrets
import uuid

logger = logging.getLogger(__name__)


@activity.defn
async def create_user(phone_number: str) -> Dict[str, Any]:
    """
    Create new user in database
    
    Args:
        phone_number: User's WhatsApp number
    
    Returns:
        User data dict
    """
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.whatsapp_number == phone_number).first()
        if existing_user:
            logger.info(f"User already exists: {phone_number}")
            # Generate new verification code for existing incomplete registrations
            if not existing_user.registration_completed:
                verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
                existing_user.verification_code = verification_code
                existing_user.verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
                db.commit()
            else:
                verification_code = None
            
            return {
                "id": existing_user.id,
                "phone_number": existing_user.whatsapp_number,
                "verification_code": verification_code,
                "is_verified": existing_user.is_verified,
                "registration_completed": existing_user.registration_completed
            }
        
        # Generate verification code
        verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Create user
        user = User(
            id=phone_number,
            whatsapp_number=phone_number,
            verification_code=verification_code,
            verification_code_expires=datetime.utcnow() + timedelta(minutes=10)
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created user: {phone_number}")
        
        return {
            "id": user.id,
            "phone_number": user.whatsapp_number,
            "verification_code": verification_code,
            "is_verified": False,
            "registration_completed": False
        }
    
    finally:
        db.close()


@activity.defn
async def verify_user_code(phone_number: str, code: str) -> bool:
    """
    Verify user's verification code
    
    Args:
        phone_number: User's phone number
        code: Verification code to check
    
    Returns:
        True if code is valid, False otherwise
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.whatsapp_number == phone_number).first()
        
        if not user:
            logger.warning(f"User not found: {phone_number}")
            return False
        
        if user.is_verified:
            logger.info(f"User already verified: {phone_number}")
            return True
        
        if user.verification_code != code:
            logger.warning(f"Invalid code for user: {phone_number}")
            return False
        
        if datetime.utcnow() > user.verification_code_expires:
            logger.warning(f"Expired code for user: {phone_number}")
            return False
        
        # Mark as verified and generate nonce
        user.is_verified = True
        user.nonce = secrets.token_urlsafe(32)
        db.commit()
        
        logger.info(f"User verified: {phone_number}")
        return True
    
    finally:
        db.close()


@activity.defn
async def get_user(phone_number: str) -> Optional[Dict[str, Any]]:
    """Get user data by phone number"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.whatsapp_number == phone_number).first()
        
        if not user:
            return None
        
        return {
            "id": user.id,
            "phone_number": user.whatsapp_number,
            "is_verified": user.is_verified,
            "registration_completed": user.registration_completed,
            "circle_wallet_id": user.circle_wallet_id,
            "circle_wallet_address": user.circle_wallet_address,
            "has_pin": user.pin_hash is not None
        }
    
    finally:
        db.close()


@activity.defn
async def update_user_pin(phone_number: str, pin_hash: str) -> bool:
    """Update user's PIN hash"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.whatsapp_number == phone_number).first()
        
        if not user:
            logger.error(f"User not found: {phone_number}")
            return False
        
        user.pin_hash = pin_hash
        db.commit()
        
        logger.info(f"PIN updated for user: {phone_number}")
        return True
    
    finally:
        db.close()


@activity.defn
async def update_user_wallet(phone_number: str, wallet_id: str, wallet_address: str) -> bool:
    """Update user's Circle wallet information"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.whatsapp_number == phone_number).first()
        
        if not user:
            logger.error(f"User not found: {phone_number}")
            return False
        
        user.circle_wallet_id = wallet_id
        user.circle_wallet_address = wallet_address
        user.registration_completed = True
        db.commit()
        
        logger.info(f"Wallet updated for user: {phone_number}")
        return True
    
    finally:
        db.close()


@activity.defn
async def log_message(
    phone_number: str,
    direction: str,
    message_body: str,
    message_sid: Optional[str] = None,
    intent: Optional[str] = None,
    workflow_id: Optional[str] = None
) -> str:
    """Log message to database"""
    db = SessionLocal()
    try:
        message = Message(
            user_id=phone_number,
            direction=direction,
            message_body=message_body,
            message_sid=message_sid,
            intent=intent,
            workflow_id=workflow_id
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        logger.info(f"Logged {direction} message for {phone_number}")
        return str(message.id)
    
    finally:
        db.close()


@activity.defn
async def create_transaction(
    phone_number: str,
    transaction_type: str,
    amount: float,
    recipient: Optional[str] = None,
    recipient_address: Optional[str] = None
) -> str:
    """Create transaction record"""
    db = SessionLocal()
    try:
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=phone_number,
            transaction_type=transaction_type,
            amount=amount,
            recipient=recipient,
            recipient_address=recipient_address,
            status="pending"
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Created transaction {transaction.id} for {phone_number}")
        return transaction.id
    
    finally:
        db.close()


@activity.defn
async def update_transaction_status(
    transaction_id: str,
    status: str,
    tx_hash: Optional[str] = None
) -> bool:
    """Update transaction status"""
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            logger.error(f"Transaction not found: {transaction_id}")
            return False
        
        transaction.status = status
        if tx_hash:
            transaction.tx_hash = tx_hash
        if status == "confirmed":
            transaction.confirmed_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Transaction {transaction_id} updated to {status}")
        return True
    
    finally:
        db.close()