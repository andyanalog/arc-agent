import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from circle_api import circle_api

async def test_wallet_creation():
    """Test wallet creation via REST API"""
    try:
        # Create wallet set
        wallet_set_response = circle_api.create_wallet_set("ArcAgent Test")
        wallet_set_id = wallet_set_response['data']['walletSet']['id']
        print(f"✅ Wallet set created: {wallet_set_id}")
        
        # Create wallet
        wallet_response = circle_api.create_wallet(wallet_set_id, "ARC-TESTNET")
        wallet = wallet_response['data']['wallets'][0]
        
        print(f"✅ Wallet created!")
        print(f"  ID: {wallet['id']}")
        print(f"  Address: {wallet['address']}")
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        
        # Print the actual error response
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_wallet_creation())