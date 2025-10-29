from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Temporal
    TEMPORAL_HOST: str
    TEMPORAL_NAMESPACE: str
    TEMPORAL_TASK_QUEUE: str
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str
    
    # Security
    PIN_SALT: str 
    SESSION_SECRET: str
    
    # Circle
    CIRCLE_API_KEY: str 
    CIRCLE_ENTITY_SECRET: str
    
    # Arc
    ARC_RPC_URL: str 
    ARC_CHAIN_ID: int
    
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