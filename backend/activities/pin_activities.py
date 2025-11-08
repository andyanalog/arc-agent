from temporalio import activity
from models.database import User, SessionLocal
from utils.security import verify_pin
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@activity.defn
async def verify_user_pin(phone_number: str, provided_pin_hash: str) -> Dict[str, Any]:
    """
    Verify user's PIN for transaction authorization
    
    Args:
        phone_number: User's phone number
        provided_pin_hash: Client-side SHA256 hash of the PIN
    
    Returns:
        Dict with verification result
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.whatsapp_number == phone_number).first()
        
        if not user:
            logger.warning(f"User not found: {phone_number}")
            return {
                "verified": False,
                "error": "user_not_found"
            }
        
        if not user.pin_hash:
            logger.warning(f"User has no PIN set: {phone_number}")
            return {
                "verified": False,
                "error": "pin_not_set"
            }
        
        # Verify the PIN (stored hash is Argon2 of client SHA256)
        is_valid = verify_pin(user.pin_hash, provided_pin_hash)
        
        if is_valid:
            logger.info(f"PIN verified successfully for {phone_number}")
            return {
                "verified": True,
                "user_id": user.id
            }
        else:
            logger.warning(f"Invalid PIN for {phone_number}")
            return {
                "verified": False,
                "error": "invalid_pin"
            }
    
    except Exception as e:
        logger.error(f"PIN verification error: {str(e)}")
        return {
            "verified": False,
            "error": "verification_failed"
        }
    
    finally:
        db.close()