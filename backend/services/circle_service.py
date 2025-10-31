import requests
import logging
import uuid
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from config import settings

logger = logging.getLogger(__name__)


class CircleService:
    """Circle API service for wallet operations"""
    
    def __init__(self):
        self.api_key = settings.CIRCLE_API_KEY
        self.entity_secret = settings.CIRCLE_ENTITY_SECRET
        self.base_url = "https://api.circle.com/v1/w3s"
        self._public_key = None
        
    def _get_headers(self) -> Dict[str, str]:
        """Get common request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get_public_key(self):
        """Get Circle's public key (cached)"""
        if self._public_key is None:
            url = "https://api.circle.com/v1/w3s/config/entity/publicKey"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            public_key_pem = response.json()['data']['publicKey']
            self._public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
        return self._public_key
    
    def _get_entity_secret_ciphertext(self) -> str:
        """Encrypt entity secret for this request"""
        public_key = self._get_public_key()
        entity_secret_bytes = bytes.fromhex(self.entity_secret)
        
        encrypted = public_key.encrypt(
            entity_secret_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted).decode()
    
    def create_wallet_set(self, name: str) -> Dict[str, Any]:
        """Create a wallet set"""
        url = f"{self.base_url}/developer/walletSets"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "entitySecretCiphertext": self._get_entity_secret_ciphertext(),
            "name": name
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_wallet(self, wallet_set_id: str, blockchain: str = "ARC-TESTNET") -> Dict[str, Any]:
        """Create a wallet on specified blockchain"""
        url = f"{self.base_url}/developer/wallets"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "entitySecretCiphertext": self._get_entity_secret_ciphertext(),
            "accountType": "SCA",
            "blockchains": [blockchain],
            "count": 1,
            "walletSetId": wallet_set_id
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_wallet_balance(self, wallet_id: str) -> Dict[str, Any]:
        """Get wallet balance"""
        url = f"{self.base_url}/wallets/{wallet_id}/balances"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def create_user_wallet(self, user_id: str) -> Dict[str, str]:
        """Create complete wallet for user"""
        wallet_set_response = self.create_wallet_set(f"ArcAgent-{user_id}")
        wallet_set_id = wallet_set_response['data']['walletSet']['id']
        
        wallet_response = self.create_wallet(wallet_set_id, "ARC-TESTNET")
        wallet = wallet_response['data']['wallets'][0]
        
        return {
            "wallet_id": wallet['id'],
            "wallet_address": wallet['address']
        }


circle_service = CircleService()