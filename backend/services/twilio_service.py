from twilio.rest import Client
from config import settings
from typing import Optional
import logging
import requests

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
        explorer_url = f"https://testnet.arcscan.app/tx/{tx_hash}"
        
        body = f"""✅ Payment Successful!

Amount: ${amount:.2f}
To: {recipient}
Tx Hash: {tx_hash[:10]}...{tx_hash[-8:]}
Time: {timestamp}

View on explorer:
{explorer_url}

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
    
    def upload_media_to_twilio(self, audio_data: bytes, filename: str = "audio.mp3") -> str:
        """
        Upload media to Twilio and get public URL
        
        Args:
            audio_data: Audio file bytes
            filename: Name of the file
            
        Returns:
            Public media URL
        """
        try:
            # Upload using Twilio's Media API
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages/Media.json"
            
            files = {
                'MediaFile': (filename, audio_data, 'audio/mpeg')
            }
            
            response = requests.post(
                url,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                files=files
            )
            
            if response.status_code == 201:
                media_data = response.json()
                media_url = f"https://api.twilio.com{media_data['uri'].replace('.json', '')}"
                logger.info(f"Media uploaded to Twilio: {media_url}")
                return media_url
            else:
                logger.error(f"Failed to upload media: {response.status_code} - {response.text}")
                raise Exception(f"Media upload failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to upload media to Twilio: {str(e)}")
            raise
    
    def send_audio_message(self, to: str, audio_data: bytes) -> str:
        """
        Send audio message via WhatsApp
        
        Args:
            to: Recipient WhatsApp number
            audio_data: Audio file data as bytes
            
        Returns:
            Message SID
        """
        try:
            # Ensure 'to' has whatsapp: prefix
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            
            # Method 1: Try uploading to a temporary public storage service
            # For now, we'll use tmpfiles.org which provides temporary public URLs
            
            logger.info(f"Uploading audio to temporary storage...")
            
            # Upload to tmpfiles.org (free temporary file hosting)
            upload_response = requests.post(
                'https://tmpfiles.org/api/v1/upload',
                files={'file': ('audio.mp3', audio_data, 'audio/mpeg')}
            )
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                if result.get('status') == 'success':
                    # Get the URL and convert it to direct link
                    file_url = result['data']['url']
                    # Convert https://tmpfiles.org/12345 to https://tmpfiles.org/dl/12345
                    direct_url = file_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
                    
                    logger.info(f"Audio uploaded to: {direct_url}")
                    
                    # Send message with media
                    message = self.client.messages.create(
                        from_=self.from_number,
                        to=to,
                        media_url=[direct_url]
                    )
                    
                    logger.info(f"Audio message sent to {to}: {message.sid}")
                    return message.sid
            
            # If tmpfiles fails, raise exception
            raise Exception("Failed to upload audio to temporary storage")
            
        except Exception as e:
            logger.error(f"Failed to send audio message to {to}: {str(e)}")
            raise


# Singleton instance
twilio_service = TwilioService()