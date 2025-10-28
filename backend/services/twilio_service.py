from twilio.rest import Client
from config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TwilioService:
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER
    
    def send_message(
        self,
        to: str,
        body: str,
        content_sid: Optional[str] = None,
        content_variables: Optional[dict] = None
    ) -> str:
        """
        Send WhatsApp message via Twilio
        
        Args:
            to: Recipient WhatsApp number (format: whatsapp:+1234567890)
            body: Message text
            content_sid: Optional Twilio content template SID
            content_variables: Optional variables for content template
            
        Returns:
            Message SID
        """
        try:
            # Ensure 'to' has whatsapp: prefix
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            
            message_params = {
                'from_': self.from_number,
                'to': to,
            }
            
            # Use content template if provided
            if content_sid:
                message_params['content_sid'] = content_sid
                if content_variables:
                    import json
                    message_params['content_variables'] = json.dumps(content_variables)
            else:
                message_params['body'] = body
            
            message = self.client.messages.create(**message_params)
            
            logger.info(f"Message sent to {to}: {message.sid}")
            return message.sid
            
        except Exception as e:
            logger.error(f"Failed to send message to {to}: {str(e)}")
            raise
    
    def send_verification_code(self, to: str, code: str) -> str:
        """Send verification code message"""
        body = f"🔐 Your ArcAgent verification code is: {code}\n\nThis code expires in 10 minutes."
        return self.send_message(to, body)
    
    def send_welcome_message(self, to: str, user_name: Optional[str] = None) -> str:
        """Send welcome message after registration"""
        greeting = f"Welcome{' ' + user_name if user_name else ''} to ArcAgent! 🚀"
        body = f"""{greeting}

Your wallet is ready! Here's what you can do:

💸 Send money: "Send $20 to John"
💰 Check balance: "Balance" or "How much do I have?"
📊 View history: "Show transactions"
⚙️ Settings: "Settings"

Need help? Just type "Help"
        """
        return self.send_message(to, body)
    
    def send_confirmation_request(
        self,
        to: str,
        action: str,
        amount: Optional[float] = None,
        recipient: Optional[str] = None
    ) -> str:
        """Request user confirmation for an action"""
        if amount and recipient:
            body = f"💸 You want to send ${amount:.2f} to {recipient}.\n\nReply CONFIRM to proceed or CANCEL to abort."
        else:
            body = f"⚠️ Confirm action: {action}\n\nReply CONFIRM to proceed or CANCEL to abort."
        
        return self.send_message(to, body)
    
    def send_transaction_receipt(
        self,
        to: str,
        amount: float,
        recipient: str,
        tx_hash: str,
        timestamp: str
    ) -> str:
        """Send transaction receipt"""
        body = f"""✅ Payment Successful!

Amount: ${amount:.2f}
To: {recipient}
Tx Hash: {tx_hash[:10]}...{tx_hash[-8:]}
Time: {timestamp}

Your balance has been updated.
        """
        return self.send_message(to, body)
    
    def send_error_message(self, to: str, error_type: str = "general") -> str:
        """Send error message"""
        error_messages = {
            "insufficient_funds": "❌ Insufficient funds. Please check your balance and try again.",
            "invalid_recipient": "❌ Invalid recipient. Please check the name or number and try again.",
            "invalid_amount": "❌ Invalid amount. Please enter a valid dollar amount.",
            "general": "❌ Something went wrong. Please try again or contact support.",
            "rate_limit": "⏳ Too many requests. Please wait a moment and try again."
        }
        
        body = error_messages.get(error_type, error_messages["general"])
        return self.send_message(to, body)


# Singleton instance
twilio_service = TwilioService()