from circle.web3.developer_controlled_wallets import ApiClient, Configuration
from config import settings
import logging

logger = logging.getLogger(__name__)


class CircleConfig:
    """Circle SDK configuration and client initialization"""
    
    def __init__(self):
        self.api_key = settings.CIRCLE_API_KEY
        self.entity_secret = settings.CIRCLE_ENTITY_SECRET
        self.client = None
        
    def get_client(self):
        """Initialize and return Circle client"""
        if not self.client:
            try:
                configuration = Configuration(
                    api_key=self.api_key,
                    entity_secret=self.entity_secret
                )
                # Use production endpoint (testnet keys work here)
                configuration.host = "https://api.circle.com"
                
                self.client = ApiClient(configuration)
                
                logger.info("Circle client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Circle client: {str(e)}")
                raise
        
        return self.client


# Singleton instance
circle_config = CircleConfig()