import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add debug prints for environment setup
print("Current working directory:", os.getcwd())
print("Python path:", sys.path)

# Ensure we load the .env from the correct location
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

# Debug print for API key (first few characters only)
api_key = os.getenv('API_KEY')
if api_key:
    print(f"API key found: {api_key[:8]}...")
else:
    print("No API key found!")

from ..api.livecoinwatch import LiveCoinWatchClient

def test_api():
    try:
        client = LiveCoinWatchClient()
        
        # Test all our mapped tokens
        test_cases = [
            'native',                                         # PLS
            '0xa1077a294dde1b09bb078844df40758a5d0f9a27',   # WPLS
            '0x95b303987a60c71504d99aa1b13b4da07b0790ab',   # PLSX
            '0x57fde0a71132198bbec939b98976993d8d89d225',   # HEX (ETH)
            '0x2b591e99afe9f32eaa6214f7b7629768c40eeb39',   # HEX (PLS)
            '0x2fa878ab3f87cc1c9737fc071108f904c0b0c95d',   # INC
            '0x6b175474e89094c44da98b954eedeac495271d0f',   # pDAI
        ]
        
        for address in test_cases:
            print(f"\nTesting address: {address}")
            result = client.get_token_info(address)
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
if __name__ == "__main__":
    test_api()
