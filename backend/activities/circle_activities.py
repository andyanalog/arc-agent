from temporalio import activity
from typing import Dict, Any
import logging
import uuid
import random

logger = logging.getLogger(__name__)


# DUMMY IMPLEMENTATIONS - Will be replaced with actual Circle API calls


@activity.defn
async def create_circle_wallet(user_id: str) -> Dict[str, str]:
    """
    Create Circle wallet for user (DUMMY)
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with wallet_id and wallet_address
    """
    logger.info(f"[DUMMY] Creating Circle wallet for user: {user_id}")
    
    # Simulate API call delay
    import asyncio
    await asyncio.sleep(0.5)
    
    # Generate dummy wallet data
    wallet_id = f"wallet_{uuid.uuid4().hex[:16]}"
    wallet_address = f"0x{uuid.uuid4().hex[:40]}"
    
    logger.info(f"[DUMMY] Created wallet: {wallet_id}, address: {wallet_address}")
    
    return {
        "wallet_id": wallet_id,
        "wallet_address": wallet_address
    }


@activity.defn
async def get_wallet_balance(wallet_id: str) -> float:
    """
    Get wallet USDC balance (DUMMY)
    
    Args:
        wallet_id: Circle wallet ID
    
    Returns:
        Balance in USDC
    """
    logger.info(f"[DUMMY] Getting balance for wallet: {wallet_id}")
    
    # Return random balance for testing
    balance = round(random.uniform(10, 500), 2)
    
    logger.info(f"[DUMMY] Wallet {wallet_id} balance: ${balance}")
    return balance


@activity.defn
async def initiate_transfer(
    from_wallet_id: str,
    to_address: str,
    amount: float
) -> Dict[str, Any]:
    """
    Initiate USDC transfer via Circle (DUMMY)
    
    Args:
        from_wallet_id: Source wallet ID
        to_address: Destination wallet address
        amount: Amount in USDC
    
    Returns:
        Dict with transfer_id and status
    """
    logger.info(f"[DUMMY] Initiating transfer from {from_wallet_id} to {to_address}: ${amount}")
    
    # Simulate API call
    import asyncio
    await asyncio.sleep(1)
    
    transfer_id = f"transfer_{uuid.uuid4().hex[:16]}"
    
    logger.info(f"[DUMMY] Transfer initiated: {transfer_id}")
    
    return {
        "transfer_id": transfer_id,
        "status": "pending"
    }


@activity.defn
async def check_transfer_status(transfer_id: str) -> Dict[str, Any]:
    """
    Check Circle transfer status (DUMMY)
    
    Args:
        transfer_id: Circle transfer ID
    
    Returns:
        Dict with status and tx_hash
    """
    logger.info(f"[DUMMY] Checking transfer status: {transfer_id}")
    
    # Simulate successful transfer
    tx_hash = f"0x{uuid.uuid4().hex}"
    
    return {
        "transfer_id": transfer_id,
        "status": "confirmed",
        "tx_hash": tx_hash
    }


@activity.defn
async def resolve_recipient_address(recipient_identifier: str) -> str:
    """
    Resolve recipient name/phone to wallet address (DUMMY)
    
    Args:
        recipient_identifier: Name, phone, or ENS
    
    Returns:
        Wallet address
    """
    logger.info(f"[DUMMY] Resolving recipient: {recipient_identifier}")
    
    # For now, generate dummy address
    # In production, this would query internal user DB or ENS
    address = f"0x{uuid.uuid4().hex[:40]}"
    
    logger.info(f"[DUMMY] Resolved {recipient_identifier} to {address}")
    return address