from fastapi import HTTPException, Header
from temporalio.client import Client
import logging
from config import settings

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from Cloudflare Worker"""
    expected_key = settings.BACKEND_API_KEY
    if x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


async def get_temporal_client() -> Client:
    """Get Temporal client instance"""
    return await Client.connect(settings.TEMPORAL_HOST)