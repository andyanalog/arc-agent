import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://arcagent:arcagent_dev_password@localhost:5432/arcagent"
    
    # Temporal
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "arcagent-task-queue"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    
    # Security
    PIN_SALT: str = "arcagent-dev-salt-change-in-production"
    SESSION_SECRET: str = "dev-secret-key-change-in-production"
    BACKEND_API_KEY: str = "dev-api-key-change-in-production"
    BACKEND_PUBLIC_URL: str = "https://124323597a66.ngrok-free.app"
    
    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice (Rachel)
    
    # Circle
    CIRCLE_API_KEY: str
    CIRCLE_ENTITY_SECRET: str
    CIRCLE_USDC_TOKEN_ID: str = "0x3600000000000000000000000000000000000000"
    
    # Arc
    ARC_RPC_URL: str = "https://rpc.testnet.arc.network"
    ARC_CHAIN_ID: int = 5042002
    
    # Cloudflare Worker
    CLOUDFLARE_WORKER_URL: str = "https://arcagent-ai-worker.your-subdomain.workers.dev"
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()