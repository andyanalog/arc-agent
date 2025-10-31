import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from circle_activities import create_circle_wallet

async def test_activity():
    """Test the create_circle_wallet activity"""
    try:
        test_phone = "+1234567890"
        
        print(f"Testing wallet creation activity for {test_phone}...")
        result = await create_circle_wallet(test_phone)
        
        print("✅ Activity executed successfully!")
        print(f"  Wallet ID: {result['wallet_id']}")
        print(f"  Wallet Address: {result['wallet_address']}")
        
    except Exception as e:
        print(f"❌ Activity failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_activity())