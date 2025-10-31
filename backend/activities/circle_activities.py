import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from temporalio import activity
from typing import Dict, Any
import logging
from services.circle_service import circle_service

logger = logging.getLogger(__name__)


@activity.defn
async def create_circle_wallet(user_id: str) -> Dict[str, str]:
    """Create Circle wallet for user on Arc Testnet"""
    logger.info(f"Creating Circle wallet for user: {user_id}")
    
    try:
        result = circle_service.create_user_wallet(user_id)
        logger.info(f"Created wallet: {result['wallet_id']}, address: {result['wallet_address']}")
        return result
    except Exception as e:
        logger.error(f"Failed to create Circle wallet: {str(e)}")
        raise


@activity.defn
async def get_wallet_balance(wallet_id: str) -> float:
    """Get wallet USDC balance"""
    logger.info(f"Getting balance for wallet: {wallet_id}")
    
    try:
        balance_response = circle_service.get_wallet_balance(wallet_id)
        token_balances = balance_response['data']['tokenBalances']
        
        logger.info(f"Token balances response: {token_balances}")
        
        for token_balance in token_balances:
            token = token_balance['token']
            symbol = token['symbol']
            
            # Match USDC or USDC-TESTNET
            if 'USDC' in symbol:
                amount = float(token_balance['amount'])
                logger.info(f"Wallet {wallet_id} balance: {amount} {symbol}")
                return amount
        
        logger.warning(f"No USDC balance found for wallet {wallet_id}")
        return 0.0
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {str(e)}")
        return 0.0


@activity.defn
async def initiate_transfer(from_wallet_id: str, to_address: str, amount: float) -> Dict[str, Any]:
    """Initiate transfer (placeholder)"""
    logger.info(f"[PLACEHOLDER] Transfer: {from_wallet_id} -> {to_address}: ${amount}")
    import uuid
    return {"transfer_id": f"transfer_{uuid.uuid4().hex[:16]}", "status": "pending"}


@activity.defn
async def check_transfer_status(transfer_id: str) -> Dict[str, Any]:
    """Check transfer status (placeholder)"""
    logger.info(f"[PLACEHOLDER] Checking transfer: {transfer_id}")
    import uuid
    return {"transfer_id": transfer_id, "status": "confirmed", "tx_hash": f"0x{uuid.uuid4().hex}"}


@activity.defn
async def resolve_recipient_address(recipient_identifier: str) -> str:
    """Resolve recipient (placeholder)"""
    logger.info(f"[PLACEHOLDER] Resolving recipient: {recipient_identifier}")
    import uuid
    return f"0x{uuid.uuid4().hex[:40]}"