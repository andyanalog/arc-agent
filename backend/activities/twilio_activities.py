from temporalio import activity
from services.twilio_service import twilio_service
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@activity.defn
async def send_verification_code(phone_number: str, code: str) -> str:
    """
    Send verification code to user's WhatsApp
    
    Args:
        phone_number: User's phone number (format: +1234567890)
        code: 6-digit verification code
    
    Returns:
        Message SID from Twilio
    """
    logger.info(f"Sending verification code to {phone_number}")
    
    # In development, log the code
    if logger.level == logging.DEBUG:
        logger.debug(f"Verification code for {phone_number}: {code}")
    
    message_sid = twilio_service.send_verification_code(phone_number, code)
    return message_sid


@activity.defn
async def send_welcome_message(phone_number: str, user_name: Optional[str] = None) -> str:
    """Send welcome message after successful registration"""
    logger.info(f"Sending welcome message to {phone_number}")
    message_sid = twilio_service.send_welcome_message(phone_number, user_name)
    return message_sid


@activity.defn
async def send_pin_setup_link(phone_number: str, setup_token: str) -> str:
    """
    Send secure PIN setup link
    
    Args:
        phone_number: User's phone number
        setup_token: Secure token for PIN setup
    
    Returns:
        Message SID
    """
    logger.info(f"Sending PIN setup link to {phone_number}")
    
    # Clean phone number for URL (remove any special characters)
    from urllib.parse import quote
    clean_phone = phone_number.strip().replace(' ', '')
    
    setup_url = f"http://localhost:8000/setup-pin?token={setup_token}&phone={quote(clean_phone)}"
    
    body = f"""🔒 Secure your ArcAgent wallet!

Click the link below to set up your PIN:
{setup_url}

This link expires in 15 minutes.
Never share this link with anyone!
    """
    
    message_sid = twilio_service.send_message(phone_number, body)
    return message_sid


@activity.defn
async def send_confirmation_request(
    phone_number: str,
    action: str,
    amount: Optional[float] = None,
    recipient: Optional[str] = None
) -> str:
    """Request confirmation from user for an action"""
    logger.info(f"Requesting confirmation from {phone_number} for {action}")
    message_sid = twilio_service.send_confirmation_request(
        phone_number,
        action,
        amount,
        recipient
    )
    return message_sid


@activity.defn
async def send_transaction_receipt(
    phone_number: str,
    amount: float,
    recipient: str,
    tx_hash: str,
    timestamp: str
) -> str:
    """Send transaction receipt to user"""
    logger.info(f"Sending receipt to {phone_number} for tx {tx_hash}")
    message_sid = twilio_service.send_transaction_receipt(
        phone_number,
        amount,
        recipient,
        tx_hash,
        timestamp
    )
    return message_sid


@activity.defn
async def send_error_message(phone_number: str, error_type: str = "general") -> str:
    """Send error message to user"""
    logger.info(f"Sending error message to {phone_number}: {error_type}")
    message_sid = twilio_service.send_error_message(phone_number, error_type)
    return message_sid


@activity.defn
async def send_custom_message(phone_number: str, message: str) -> str:
    """Send custom message to user"""
    logger.info(f"Sending custom message to {phone_number}")
    message_sid = twilio_service.send_message(phone_number, message)
    return message_sid