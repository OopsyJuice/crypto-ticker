from pylivecoinwatch import LiveCoinWatchAPI
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
                    'price_change_24h': str(result.get('delta', {}).get('day', 0))
                }
            return None

        except Exception as e:
            print(f"Error in get_token_info: {str(e)}")
            return None

    def _get_token_data(self, address: str) -> dict:
        # Enhanced token mapping with more data
        token_mapping = {
            'native': {
                'symbol': 'PLS',
                'name': 'PulseChain',
                'code': 'PLS'
            },
            '0xa1077a294dde1b09bb078844df40758a5d0f9a27': {
                'symbol': 'WPLS',
                'name': 'Wrapped PulseChain',
                'code': 'PLS'
            },
            '0x95b303987a60c71504d99aa1b13b4da07b0790ab': {
                'symbol': 'PLSX',
                'name': 'PulseX',
                'code': 'PLSX'
            },
            '0x57fde0a71132198bbec939b98976993d8d89d225': {
                'symbol': 'eHEX',
                'name': 'HEX (Ethereum)',
                'code': 'HEX'
            },
            '0x2b591e99afe9f32eaa6214f7b7629768c40eeb39': {
                'symbol': 'pHEX',
                'name': 'HEX (PulseChain)',
                'code': '___HEX',  # Updated code for PLS HEX
                'platform': 'PULSECHAIN'
            },
            '0x2fa878ab3f87cc1c9737fc071108f904c0b0c95d': {
                'symbol': 'INC',
                'name': 'Incentive',
                'code': '__INC'
            },
            '0x6b175474e89094c44da98b954eedeac495271d0f': {
                'symbol': 'pDAI',
                'name': 'DAI on PulseChain',
                'code': 'DAI'
            }
        }
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
