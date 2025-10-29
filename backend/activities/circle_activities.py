from temporalio import activity
from typing import Dict, Any
import logging
import uuid
import random
import requests
import asyncio

from backend.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = "https://api.circle.com/v1/w3s"


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.CIRCLE_API_KEY}",
        "Content-Type": "application/json",
    }


def _idem() -> str:
    return str(uuid.uuid4())




# DUMMY IMPLEMENTATIONS - Will be replaced with actual Circle API calls


@activity.defn
async def create_circle_wallet(user_id: str) -> Dict[str, str]:
    """
    Create a developer-controlled wallet for a given user via Circle API.
    """
    logger.info(f"Creating Circle wallet for user {user_id}")
    await asyncio.sleep(0)  # yield control to Temporal worker

    # Step 1: ensure wallet set exists (could store/reuse)
    wallet_set_body = {"name": f"ArcAgent_Set_{user_id}"}
    ws_resp = requests.post(
        f"{BASE_URL}/developer/walletSets", headers=_auth_headers(), json=wallet_set_body
    )
    ws_data = ws_resp.json()
    if ws_resp.status_code >= 300:
        raise RuntimeError(f"Wallet set creation failed: {ws_data}")

    wallet_set_id = ws_data.get("data", {}).get("id")
    logger.info(f"Created wallet set: {wallet_set_id}")

    # Step 2: create wallet inside that set
    wallet_body = {
        "idempotencyKey": _idem(),
        "walletSetId": wallet_set_id,
        "blockchains": ["MATIC-AMOY"],
        "count": 1,
        "accountType": "SCA",
    }

    w_resp = requests.post(
        f"{BASE_URL}/developer/wallets", headers=_auth_headers(), json=wallet_body
    )
    w_data = w_resp.json()
    if w_resp.status_code >= 300:
        raise RuntimeError(f"Wallet creation failed: {w_data}")

    wallet = w_data["data"]["wallets"][0]
    logger.info(f"Wallet created for user {user_id}: {wallet['id']}")

    return {
        "wallet_id": wallet["id"],
        "wallet_address": wallet["address"],
    }

@activity.defn
async def get_wallet_balance(wallet_id: str) -> float:
    logger.info(f"Getting balance for wallet {wallet_id}")
    await asyncio.sleep(0)

    url = f"{BASE_URL}/developer/wallets/{wallet_id}"
    resp = requests.get(url, headers=_auth_headers())
    data = resp.json()
    if resp.status_code >= 300:
        raise RuntimeError(f"Failed to fetch wallet: {data}")

    balances = data.get("data", {}).get("balances", [])
    usdc = next((b for b in balances if b["token"]["symbol"] == "USDC"), None)
    amount = float(usdc["amount"]) if usdc else 0.0

    logger.info(f"Wallet {wallet_id} USDC balance: {amount}")
    return amount


@activity.defn
async def initiate_transfer(
    from_wallet_id: str,
    to_address: str,
    amount: float
) -> Dict[str, Any]:
    """
    Initiate USDC transfer via Circle (DUMMY)
    """
    
    logger.info(f"Initiating transfer from {from_wallet_id} → {to_address}: {amount} USDC")
    await asyncio.sleep(0)

    body = {
        "idempotencyKey": _idem(),
        "source": {"walletId": from_wallet_id},
        "destination": {"address": to_address},
        "amount": {"amount": str(amount), "tokenId": "USDC-MATIC-AMOY"},
    }

    resp = requests.post(
        f"{BASE_URL}/developer/transactions/transfers", headers=_auth_headers(), json=body
    )
    data = resp.json()
    if resp.status_code >= 300:
        raise RuntimeError(f"Transfer failed: {data}")

    logger.info(f"Transfer initiated: {data}")
    return {
        "transfer_id": data.get("data", {}).get("id"),
        "status": data.get("data", {}).get("state", "pending"),
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
    logger.info(f"Checking transfer status for {transfer_id}")
    await asyncio.sleep(0)

    resp = requests.get(f"{BASE_URL}/developer/transactions/{transfer_id}", headers=_auth_headers())
    data = resp.json()
    if resp.status_code >= 300:
        raise RuntimeError(f"Failed to check transfer: {data}")

    return {
        "transfer_id": transfer_id,
        "status": data.get("data", {}).get("state", "unknown"),
        "tx_hash": data.get("data", {}).get("transactionHash"),
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