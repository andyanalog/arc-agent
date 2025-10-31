import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from temporalio import activity
from typing import Dict, Any
import logging
from circle_api import circle_api

logger = logging.getLogger(__name__)


@activity.defn
async def create_circle_wallet(user_id: str) -> Dict[str, str]:
    """
    Create Circle wallet for user on Arc Testnet
    
    Args:
        user_id: User identifier (phone number)
    
    Returns:
        Dict with wallet_id and wallet_address
    """
    logger.info(f"Creating Circle wallet for user: {user_id}")
    
    try:
        # Step 1: Create wallet set
        wallet_set_response = circle_api.create_wallet_set(f"ArcAgent-{user_id}")
        wallet_set_id = wallet_set_response['data']['walletSet']['id']
        
        logger.info(f"Created wallet set: {wallet_set_id}")
        
        # Step 2: Create wallet on Arc Testnet
        wallet_response = circle_api.create_wallet(wallet_set_id, "ARC-TESTNET")
        wallet = wallet_response['data']['wallets'][0]
        
        wallet_id = wallet['id']
        wallet_address = wallet['address']
        
        logger.info(f"Created wallet: {wallet_id}, address: {wallet_address}")
        
        return {
            "wallet_id": wallet_id,
            "wallet_address": wallet_address
        }
        
    except Exception as e:
        logger.error(f"Failed to create Circle wallet: {str(e)}")
        raise


# Keep other dummy functions - we'll implement next
@activity.defn
async def get_wallet_balance(wallet_id: str) -> float:
    """Get wallet USDC balance (will implement next)"""
    logger.info(f"[DUMMY] Getting balance for wallet: {wallet_id}")
    return 100.0


@activity.defn
async def initiate_transfer(from_wallet_id: str, to_address: str, amount: float) -> Dict[str, Any]:
    """Initiate transfer (will implement next)"""
    logger.info(f"[DUMMY] Transfer: {from_wallet_id} -> {to_address}: ${amount}")
    import uuid
    return {"transfer_id": f"transfer_{uuid.uuid4().hex[:16]}", "status": "pending"}


@activity.defn
async def check_transfer_status(transfer_id: str) -> Dict[str, Any]:
    """Check transfer status (will implement next)"""
    logger.info(f"[DUMMY] Checking transfer: {transfer_id}")
    import uuid
    return {"transfer_id": transfer_id, "status": "confirmed", "tx_hash": f"0x{uuid.uuid4().hex}"}


@activity.defn
async def resolve_recipient_address(recipient_identifier: str) -> str:
    """Resolve recipient (will implement next)"""
    logger.info(f"[DUMMY] Resolving recipient: {recipient_identifier}")
    import uuid
    return f"0x{uuid.uuid4().hex[:40]}"