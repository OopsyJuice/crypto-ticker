from pylivecoinwatch import LiveCoinWatchAPI
from .token_mapping import token_mapping
import os
from dotenv import load_dotenv

class LiveCoinWatchClient:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")
        print(f"Initializing with API key: {self.api_key[:8]}...")  # Debug line
        self.client = LiveCoinWatchAPI(self.api_key)

    def get_token_info(self, address: str) -> dict:
        try:
            # Handle PLS (native token) specially
            if address.lower() == 'native':
                symbol = 'PLS'
                name = 'PulseChain'
                code = 'PLS'
                platform = None
            else:
                # Get token data from mapping
                token_data = self._get_token_data(address)
                if not token_data:
                    print(f"No token data found for address: {address}")
                    return None
                symbol = token_data['symbol']
                name = token_data['name']
                code = token_data['code']
                platform = token_data.get('platform')  # Get platform if specified
            
            # Add platform parameter for specific tokens
            params = {
                'code': code,
                'currency': 'USD',
                'meta': True
            }
            if platform:
                params['platform'] = platform

            result = self.client.coins_single(**params)
            
            if result:
                return {
                    'address': address,
                    'symbol': symbol,
                    'name': name,
                    'price_usd': str(result.get('rate', 0)),
                    'price_change_24h': str(result.get('delta', {}).get('day', 0)),
                    'logo': result.get('png64', '')  # Add logo URL
                }
            return None

        except Exception as e:
            print(f"Error in get_token_info: {str(e)}")
            return None

    def _get_token_data(self, address: str) -> dict:
        return token_mapping.get(address.lower())


    def update_cached_tokens(self, addresses: list) -> dict:
        tokens = {}
        for address in addresses:
            token_info = self.get_token_info(address)
            if token_info:
                tokens[address] = token_info
        return tokens

    def __del__(self):
        # Remove the close() call since it's not supported
        pass

def get_token_info(token_code):
    if token_code in token_mapping:
        return token_mapping[token_code]
    else:
        return None

