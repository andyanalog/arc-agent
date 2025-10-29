"""
Circle Service — Developer Controlled Wallet Integration
---------------------------------------------------------
Handles Circle API calls for wallet sets, wallets, and token transfers
using the official Circle Developer Controlled Wallets SDK.
"""

from circle.web3 import developer_controlled_wallets
from config import settings
import logging
import uuid

logger = logging.getLogger(__name__)

class CircleService:
    """
    Service wrapper around Circle Developer-Controlled Wallets SDK.
    Provides methods to create wallet sets, wallets, and initiate transfers.
    """

    def __init__(self):
        try:
            self.client = developer_controlled_wallets(
                api_key=settings.CIRCLE_API_KEY,
                entity_secret=settings.CIRCLE_ENTITY_SECRET
            )
            logger.info("Circle SDK client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Circle client: {e}")
            raise

    def create_wallet_set(self, name: str):
        """Create a developer-controlled wallet set."""
        try:
            response = self.client.create_wallet_set(name=name)
            wallet_set_id = response.get("data", {}).get("id")
            logger.info(f"Wallet set created: {wallet_set_id}")
            return response
        except Exception as e:
            logger.error(f"failed to create wallet set: {e}")
            raise


    def create_wallets(
            self,
            wallet_set_id: str,
            count: int = 1,
            blockchains: list[str] = ["MATIC-AMOY"],
            account_type: str = "SCA", 
    ):
        
        try:
            idempotency_key = str(uuid.uuid4())
            response = self.client.create_wallets(
                idempotencyKey=idempotency_key,
                walletSetId=wallet_set_id,
                blockchains=blockchains,
                count=count,
                accountType=account_type,
            )
            logger.info(f"Wallet(s) created under set {wallet_set_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to create wallet(s): {e}")
            raise


    def transfer_usdc(
            self,
            source_wallet_id: str,
            destination_address: str,
            amount: str,
            token_id: str,
    ):
        """
        Transfer USDC between wallets.
        - token_id is the token identifier on a supported blockchain
          (use Circle docs to fetch USDC token ID for your target chain)
        """
        try:
            idempotency_key = str(uuid.uuid4())
            response = self.client.create_transfer(
                idempotencyKey=idempotency_key,
                source=source_wallet_id,
                destination_address=destination_address,
                amount=amount,
                token_id=token_id
            )
            logger.info(
                f"Transfer initiated: {amount} {token_id} from {source_wallet_id} → {destination_address}"
            )
            return response
        except Exception as e:
            logger.error(f"Failed to transfer USDC: {e}")
            raise

# 🧪 Quick test
# -------------------------------------------------------------
if __name__ == "__main__":
    service = CircleService()

    # Create wallet set
    ws = service.create_wallet_set("ArcAgent Dev Wallet Set")
    print(ws)

    # Create one wallet (test)
    wallet_set_id = ws.get("data", {}).get("id")
    wallet = service.create_wallets(wallet_set_id)
    print(wallet)