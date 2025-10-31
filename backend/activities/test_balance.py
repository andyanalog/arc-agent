import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from circle_api import circle_api

async def test_balance():
    """Test getting wallet balance"""
    try:
        # Replace with one of your actual wallet IDs
        wallet_id = input("Enter your wallet ID: ")
        
        print(f"Getting balance for wallet: {wallet_id}...")
        balance_response = circle_api.get_wallet_balance(wallet_id)
        
        print("✅ Balance retrieved!")
        print(f"Response: {balance_response}")
        
        # Parse token balances
        token_balances = balance_response['data']['tokenBalances']
        print(f"\nFound {len(token_balances)} tokens:")
        
        for token_balance in token_balances:
            token = token_balance['token']
            amount = token_balance['amount']
            print(f"  - {token['symbol']}: {amount} (decimals: {token['decimals']})")
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_balance())