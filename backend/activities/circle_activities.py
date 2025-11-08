import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from temporalio import activity
from typing import Dict, Any
import logging
from services.circle_service import circle_service
import asyncio

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
                # Parse amount properly - Circle returns string
                amount_str = token_balance['amount']
                amount = float(amount_str) if amount_str else 0.0
                
                logger.info(f"Wallet {wallet_id} balance: {amount} {symbol} (raw: {amount_str})")
                return amount
        
        logger.warning(f"No USDC balance found for wallet {wallet_id}")
        logger.info(f"Available tokens: {[tb['token']['symbol'] for tb in token_balances]}")
        return 0.0
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {str(e)}")
        logger.exception(e)
        return 0.0


@activity.defn
async def initiate_transfer(from_wallet_id: str, to_address: str, amount: float) -> Dict[str, Any]:
    """Initiate transfer via Circle"""
    logger.info(f"Initiating transfer: {from_wallet_id} -> {to_address}: ${amount}")
    
    try:
        from config import settings
        
        # Get token ID from wallet balance
        balance_response = circle_service.get_wallet_balance(from_wallet_id)
        token_balances = balance_response['data']['tokenBalances']
        
        token_id = None
        for token_balance in token_balances:
            token = token_balance['token']
            if 'USDC' in token['symbol']:
                token_id = token['id']
                logger.info(f"Found USDC token ID: {token_id}")
                break
        
        if not token_id:
            # Fallback to config if available
            token_id = settings.CIRCLE_USDC_TOKEN_ID
            if not token_id:
                raise Exception("USDC token not found in wallet")
        
        logger.info(f"Using token ID: {token_id}")
        
        # Convert amount to string
        amount_str = str(amount)
        
        # Create transfer transaction
        transfer_response = circle_service.create_transaction_transfer(
            wallet_id=from_wallet_id,
            token_id=token_id,
            destination_address=to_address,
            amount=amount_str
        )
        
        transaction_id = transfer_response['data']['id']
        status = transfer_response['data']['state']
        
        logger.info(f"Transfer initiated: {transaction_id}, status: {status}")
        
        return {
            "transfer_id": transaction_id,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate transfer: {str(e)}")
        raise


@activity.defn
async def check_transfer_status(transfer_id: str) -> Dict[str, Any]:
    """Check transfer status and wait for tx_hash"""
    logger.info(f"Checking transfer status: {transfer_id}")
    
    try:
        max_attempts = 60
        attempt = 0
        
        while attempt < max_attempts:
            transaction_response = circle_service.get_transaction(transfer_id)
            transaction = transaction_response['data']['transaction']
            
            status = transaction['state']
            tx_hash = transaction.get('txHash', '')
            
            logger.info(f"Transfer {transfer_id} status: {status}, tx_hash: {tx_hash} (attempt {attempt + 1}/{max_attempts})")
            
            # If we have a tx_hash, return immediately
            if tx_hash and tx_hash.startswith('0x'):
                status_map = {
                    "COMPLETE": "confirmed",
                    "PENDING_RISK_SCREENING": "pending",
                    "INITIATED": "pending",
                    "SENT": "pending",
                    "CONFIRMED": "confirmed",
                    "FAILED": "failed",
                    "DENIED": "failed"
                }
                
                return {
                    "transfer_id": transfer_id,
                    "status": status_map.get(status, "pending"),
                    "tx_hash": tx_hash
                }
            
            # Check if transaction failed
            if status in ["FAILED", "DENIED"]:
                raise Exception(f"Transfer failed with status: {status}")
            
            # Wait before next attempt
            await asyncio.sleep(3)
            attempt += 1
        
        # If we exhausted attempts without tx_hash
        logger.error(f"No tx_hash found after {max_attempts} attempts for transfer {transfer_id}")
        raise Exception("Transaction timeout: tx_hash not available")
        
    except Exception as e:
        logger.error(f"Failed to check transfer status: {str(e)}")
        raise


@activity.defn
async def resolve_recipient_address(recipient_identifier: str) -> str:
    """Resolve recipient to wallet address"""
    logger.info(f"Resolving recipient: {recipient_identifier}")
    
    # Check if it's already a wallet address (starts with 0x and 42 chars)
    if recipient_identifier.startswith('0x') and len(recipient_identifier) == 42:
        logger.info(f"Recipient is already a wallet address: {recipient_identifier}")
        return recipient_identifier
    
    # Check if it's a phone number - look up in database
    if recipient_identifier.startswith('+') or recipient_identifier.replace(' ', '').isdigit():
        from models.database import SessionLocal, User
        
        db = SessionLocal()
        try:
            # Clean phone number
            clean_phone = recipient_identifier.strip()
            if not clean_phone.startswith('+'):
                clean_phone = f"+{clean_phone}"
            
            user = db.query(User).filter(User.whatsapp_number == clean_phone).first()
            
            if user and user.circle_wallet_address:
                logger.info(f"Found user wallet: {user.circle_wallet_address}")
                return user.circle_wallet_address
            else:
                raise Exception(f"User not found or not registered: {recipient_identifier}")
        finally:
            db.close()
    
    # Try to find by user ID or name (you can extend this)
    from models.database import SessionLocal, User
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == recipient_identifier).first()
        
        if user and user.circle_wallet_address:
            logger.info(f"Found user wallet by ID: {user.circle_wallet_address}")
            return user.circle_wallet_address
        else:
            raise Exception(f"Recipient not found: {recipient_identifier}")
    finally:
        db.close()