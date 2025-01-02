import requests
from typing import Dict, List, Optional
import time
import re
import json
from pathlib import Path

class GeckoTerminalAPI:
    BASE_URL = "https://api.geckoterminal.com/api/v2"
    ETH_BASE_URL = "https://api.geckoterminal.com/api/v2/networks/eth"
    RATE_LIMIT = 25
    
    def __init__(self):
        self.session = requests.Session()
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
            # Get token info
            info_response = self.session.get(f"{self.BASE_URL}/networks/pulsechain/tokens/{address}/info")
            
            if info_response.status_code == 200:
                data = info_response.json().get('data', {})
                attrs = data.get('attributes', {})
                
                # Get basic token data
                token_data = {
                    'address': address,
                    'symbol': attrs.get('symbol', ''),
                    'name': attrs.get('name', '')
                }

                # Check if this is a bridged Ethereum token
                if "from Ethereum" in attrs.get('name', ''):
                    # For Ethereum tokens, get price from Ethereum mainnet
                    eth_pools_response = self.session.get(f"{self.ETH_BASE_URL}/tokens/{attrs.get('coingecko_coin_id', '')}/pools")
                    if eth_pools_response.status_code == 200:
                        eth_pools = eth_pools_response.json().get('data', [])
                        if eth_pools:
                            # Get the highest volume pool
                            max_volume = 0
                            best_pool = None
                            for pool in eth_pools:
                                pool_attrs = pool.get('attributes', {})
                                volume = float(pool_attrs.get('volume_usd', {}).get('h24', '0') or '0')
                                if volume > max_volume:
                                    max_volume = volume
                                    best_pool = pool
                            
                            if best_pool:
                                pool_attrs = best_pool.get('attributes', {})
                                return {
                                    **token_data,
                                    'price_usd': pool_attrs.get('base_token_price_usd', '0'),
                                    'price_change_24h': pool_attrs.get('price_change_percentage', {}).get('h24', '0')
                                }

                # If not an Ethereum token or if Ethereum price fetch fails, get PulseChain price
                pools_response = self.session.get(f"{self.BASE_URL}/networks/pulsechain/tokens/{address}/pools")
                if pools_response.status_code == 200:
                    pools_data = pools_response.json().get('data', [])
                    wpls_pool = None
                    max_volume = 0
                    
                    # Find the WPLS pool with highest volume
                    for pool in pools_data:
                        attrs = pool.get('attributes', {})
                        if 'WPLS' in attrs.get('name', ''):
                            volume = float(attrs.get('volume_usd', {}).get('h24', '0') or '0')
                            if volume > max_volume:
                                max_volume = volume
                                wpls_pool = pool
                    
                    if wpls_pool:
                        attrs = wpls_pool.get('attributes', {})
                        price_data = {
                            'price_usd': attrs.get('base_token_price_usd', '0'),
                            'price_change_24h': attrs.get('price_change_percentage', {}).get('h24', '0')
                        }
                        return {**token_data, **price_data}
            
            print(f"Error fetching complete token data for {address}")
            return None
                
        except Exception as e:
            print(f"Error fetching token info: {e}")
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