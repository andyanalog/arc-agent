import requests
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class ElevenLabsService:
    """Eleven Labs API service for STT and TTS"""
    
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"
        self.enabled = self.api_key is not None
        
        if not self.enabled:
            logger.warning("Eleven Labs API key not configured. Audio features disabled.")
    
    def _get_headers(self) -> dict:
        """Get common request headers"""
        return {
            "xi-api-key": self.api_key,
        }
    
    def transcribe_audio(self, audio_url: str) -> Optional[str]:
        """
        Transcribe audio from URL using Eleven Labs STT
        
        Args:
            audio_url: URL of the audio file to transcribe
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.enabled:
            logger.error("Eleven Labs not configured")
            return None
            
        try:
            # Download audio from Twilio URL
            logger.info(f"Downloading audio from: {audio_url}")
            audio_response = requests.get(audio_url, auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN))
            audio_response.raise_for_status()
            audio_data = audio_response.content
            
            logger.info(f"Downloaded audio: {len(audio_data)} bytes, content-type: {audio_response.headers.get('content-type')}")
            
            # Determine the correct mime type
            content_type = audio_response.headers.get('content-type', 'audio/ogg')
            
            # Map content types to file extensions
            mime_to_ext = {
                'audio/ogg': ('audio.ogg', 'audio/ogg'),
                'audio/mpeg': ('audio.mp3', 'audio/mpeg'),
                'audio/mp4': ('audio.mp4', 'audio/mp4'),
                'audio/wav': ('audio.wav', 'audio/wav'),
                'audio/webm': ('audio.webm', 'audio/webm'),
            }
            
            filename, mime = mime_to_ext.get(content_type, ('audio.ogg', content_type))
            
            # Call Eleven Labs STT API with required parameters
            url = f"{self.base_url}/speech-to-text"
            
            # Prepare multipart form data - parameter must be named 'file'
            files = {
                'file': (filename, audio_data, mime)
            }
            
            # Add required form fields
            data = {
                'model_id': 'scribe_v1',  # Required: only scribe_v1 is supported
            }
            
            headers = self._get_headers()
            
            logger.info(f"Sending to Eleven Labs STT with model: scribe_v1, filename: {filename}")
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data
            )
            
            if not response.ok:
                logger.error(f"Eleven Labs STT error: {response.status_code} - {response.text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"STT response: {result}")
            
            # Extract text from response
            # The response structure includes segments with text
            if 'text' in result:
                transcribed_text = result['text']
            elif 'segments' in result:
                # Concatenate all segment texts
                transcribed_text = ' '.join([seg.get('text', '') for seg in result.get('segments', [])])
            else:
                logger.error(f"Unexpected response format: {result}")
                return None
            
            logger.info(f"Transcribed audio: {transcribed_text[:100]}")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {str(e)}")
            logger.exception(e)
            return None
    
    def generate_speech(self, text: str) -> Optional[bytes]:
        """
        Generate speech from text using Eleven Labs TTS
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio data as bytes or None if failed
        """
        if not self.enabled:
            logger.error("Eleven Labs not configured")
            return None
            
        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(
                url,
                headers={
                    **self._get_headers(),
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            
            audio_data = response.content
            logger.info(f"Generated speech audio ({len(audio_data)} bytes)")
            return audio_data
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {str(e)}")
            return None


elevenlabs_service = ElevenLabsService()