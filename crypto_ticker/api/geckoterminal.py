import requests
from typing import Dict, List, Optional
import time
import json
from pathlib import Path

class GeckoTerminalAPI:
    BASE_URL = "https://api.geckoterminal.com/api/v2"
    ETH_BASE_URL = "https://api.geckoterminal.com/api/v2/networks/eth"
    RATE_LIMIT = 25
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })
        self.last_call_times = []
        self.backoff_time = 1

    def _rate_limit(self):
        current_time = time.time()
        self.last_call_times = [t for t in self.last_call_times if current_time - t < 60]
        
        if len(self.last_call_times) >= self.RATE_LIMIT:
            sleep_time = max(60 - (current_time - self.last_call_times[0]), self.backoff_time)
            print(f"Rate limit reached, waiting {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            self.backoff_time = min(self.backoff_time * 2, 120)
        else:
            self.backoff_time = max(1, self.backoff_time / 2)
            time.sleep(0.1)
        
        self.last_call_times.append(current_time)

    def get_token_info(self, address: str) -> Dict:
        try:
            address = address.lower()
            print(f"\n=== Getting token info for address: {address} ===")
            
            # First determine if this is a CoinGecko token
            coingecko_data = None
            if address == 'native':
                print("Identified as native PLS token")
                coingecko_data = {
                    'id': 'pulsechain',
                    'name': 'Pulse',
                    'symbol': 'PLS'
                }
            elif address == '0x1d2adcc1920dad95ca82143a5a6e4ab8662fe966':
                print("Identified as pDAI token")
                coingecko_data = {
                    'id': 'dai-on-pulsechain',
                    'name': 'DAI on PulseChain',
                    'symbol': 'pDAI'
                }

            # Handle CoinGecko tokens
            if coingecko_data:
                print(f"Fetching {coingecko_data['symbol']} price from CoinGecko...")
                print(f"Using CoinGecko ID: {coingecko_data['id']}")
                
                response = self.session.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        'ids': coingecko_data['id'],
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true'
                    }
                )
                
                print(f"CoinGecko response status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"CoinGecko response data: {data}")
                    
                    if coingecko_data['id'] in data:
                        coin_data = data[coingecko_data['id']]
                        result = {
                            'address': address,
                            'symbol': coingecko_data['symbol'],
                            'name': coingecko_data['name'],
                            'price_usd': str(coin_data['usd']),
                            'price_change_24h': str(coin_data.get('usd_24h_change', '0')),
                            'image_url': f"https://coin-images.coingecko.com/coins/images/25666/large/PLS-LogoTransparent_1.png" if address == 'native' else f"https://assets.coingecko.com/coins/images/9956/large/4943.png"
                        }
                        print(f"Returning CoinGecko data: {result}")
                        return result
                    else:
                        print(f"CoinGecko ID {coingecko_data['id']} not found in response")
                else:
                    print(f"CoinGecko API error: {response.status_code}")
                    print(f"Response content: {response.text}")
                return None

            # All other tokens use GeckoTerminal
            print(f"Using GeckoTerminal for token {address}...")
            self._rate_limit()
            info_response = self.session.get(
                f"{self.BASE_URL}/networks/pulsechain/tokens/{address}",
                headers={'Accept': 'application/json'}
            )
            
            if info_response.status_code == 200:
                data = info_response.json().get('data', {})
                attrs = data.get('attributes', {})
                
                # Get basic token data
                token_data = {
                    'address': address,
                    'symbol': attrs.get('symbol', ''),
                    'name': attrs.get('name', ''),
                    'image_url': attrs.get('image_url', '')  # Add this line
                }

                # Get highest volume pool data
                self._rate_limit()
                pools_response = self.session.get(
                    f"{self.BASE_URL}/networks/pulsechain/tokens/{address}/pools",
                    headers={'Accept': 'application/json'}
                )
                
                if pools_response.status_code == 200:
                    pools_data = pools_response.json().get('data', [])
                    if pools_data:
                        # Find highest volume pool
                        max_volume = 0
                        best_pool = None
                        for pool in pools_data:
                            attrs = pool.get('attributes', {})
                            volume = float(attrs.get('volume_usd', {}).get('h24', '0') or '0')
                            if volume > max_volume:
                                max_volume = volume
                                best_pool = pool
                        
                        if best_pool:
                            pool_attrs = best_pool.get('attributes', {})
                            token_symbol = token_data['symbol']
                            
                            # Determine if token is base or quote
                            is_base = token_symbol == pool_attrs.get('base_token_symbol', '')
                            price = pool_attrs.get('base_token_price_usd' if is_base else 'quote_token_price_usd', '0')
                            price_change = pool_attrs.get('price_change_percentage', {}).get('h24', '0')
                            
                            result = {
                                **token_data,
                                'price_usd': price,
                                'price_change_24h': price_change
                            }
                            print(f"Returning GeckoTerminal data: {result}")
                            return result
            
            print(f"Error fetching token info for {address}")
            return None
                
        except Exception as e:
            print(f"Error in get_token_info: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def _load_cache(self):
        cache_file = Path("token_cache.json")
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self, data):
        with open("token_cache.json", 'w') as f:
            json.dump(data, f)

    def update_cached_tokens(self, addresses: List[str]) -> Dict[str, Dict]:
        tokens = {}
        for address in addresses:
            token_info = self.get_token_info(address)
            if token_info:
                tokens[address] = token_info
        return tokens