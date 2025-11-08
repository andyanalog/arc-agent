import asyncio
from circle.web3.developer_controlled_wallets import ApiClient, Configuration

async def test_connection():
    """Test Circle API connection"""
    try:
        # Replace these with your actual values
        API_KEY = ""
        ENTITY_SECRET = ""
        
        configuration = Configuration(
            api_key=API_KEY,
            entity_secret=ENTITY_SECRET
        )
        client = ApiClient(configuration)
        
        print("✅ Circle client initialized successfully")
        print(f"Client type: {type(client)}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Circle client: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())