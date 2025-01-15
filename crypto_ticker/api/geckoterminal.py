import requests
from typing import Dict, List, Optional
import time
import json
from pathlib import Path

class GeckoTerminalAPI:
    BASE_URL = "https://api.geckoterminal.com/api/v2"
    ETH_BASE_URL = "https://api.geckoterminal.com/api/v2/networks/eth"
    RATE_LIMIT = 25
    COINGECKO_RATE_LIMIT = 10  # CoinGecko free API limit is 10-30 calls per minute
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })
        self.last_call_times = []
        self.last_coingecko_calls = []
        self.backoff_time = 1
        self.coingecko_backoff_time = 60  # 60 seconds backoff for CoinGecko

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

    def _coingecko_rate_limit(self):
        """Handle rate limiting for CoinGecko API calls."""
        current_time = time.time()
        self.last_coingecko_calls = [t for t in self.last_coingecko_calls if current_time - t < 60]
        
        if len(self.last_coingecko_calls) >= self.COINGECKO_RATE_LIMIT:
            sleep_time = max(60 - (current_time - self.last_coingecko_calls[0]), self.coingecko_backoff_time)
            print(f"CoinGecko rate limit reached, waiting {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        
        self.last_coingecko_calls.append(current_time)

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
            # Handle CoinGecko tokens
            if coingecko_data:
                print(f"Fetching {coingecko_data['symbol']} price from CoinGecko...")
                print(f"Using CoinGecko ID: {coingecko_data['id']}")
                
                # Try to get from cache first
                cached_data = self._load_cache()
                
                try:
                    # Apply rate limiting before CoinGecko call
                    self._coingecko_rate_limit()
                    
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
                    
                    # Handle rate limit or other errors
                    if response.status_code == 429 or response.status_code != 200:
                        print(f"CoinGecko API error: {response.status_code}")
                        print(f"Response content: {response.text}")
                        
                        # Try to use cached data
                        if address in cached_data:
                            print(f"Using cached data for {address}")
                            return cached_data[address]
                            
                        # If no cache, wait and continue
                        if response.status_code == 429:
                            time.sleep(self.coingecko_backoff_time)
                            
                except Exception as e:
                    print(f"Error in CoinGecko request: {str(e)}")
                    # Try to use cached data on error
                    if address in cached_data:
                        print(f"Using cached data after error for {address}")
                        return cached_data[address]
                
                return None

            # All other tokens use GeckoTerminal
            # All other tokens use GeckoTerminal
            print(f"Using GeckoTerminal for token {address}...")
            self._rate_limit()
            info_response = self.session.get(
                f"{self.BASE_URL}/networks/pulsechain/tokens/{address}",
                headers={'Accept': 'application/json'}
            )

            print(f"GeckoTerminal token info response: {info_response.status_code}")
            if info_response.status_code == 200:
                data = info_response.json().get('data', {})
                attrs = data.get('attributes', {})
                print(f"Token attributes: {attrs}")
                
                # Get basic token data
                token_data = {
                    'address': address,
                    'symbol': attrs.get('symbol', ''),
                    'name': attrs.get('name', ''),
                    'image_url': attrs.get('image_url', '') 
                }
                print(f"Basic token data: {token_data}")

                # Get highest volume pool data
                self._rate_limit()
                pools_response = self.session.get(
                    f"{self.BASE_URL}/networks/pulsechain/tokens/{address}/pools",
                    headers={'Accept': 'application/json'}
                )
                
                print(f"Pools response status: {pools_response.status_code}")
                if pools_response.status_code == 200:
                    pools_data = pools_response.json().get('data', [])
                    print(f"Number of pools found: {len(pools_data)}")
                    if pools_data:
                        # Find highest volume pool with valid price
                        max_volume = 0
                        best_pool = None
                        print(f"\nAnalyzing pools for {token_data['symbol']}:")
                        
                        for pool in pools_data:
                            attrs = pool.get('attributes', {})
                            volume = float(attrs.get('volume_usd', {}).get('h24', '0') or '0')
                            base_symbol = attrs.get('base_token_symbol', '')
                            quote_symbol = attrs.get('quote_token_symbol', '')
                            base_price = attrs.get('base_token_price_usd')
                            quote_price = attrs.get('quote_token_price_usd')
                            
                            print(f"\nPool: {base_symbol}-{quote_symbol}")
                            print(f"Volume: ${volume:,.2f}")
                            print(f"Base price: ${base_price}")
                            print(f"Quote price: ${quote_price}")
                            
                            # Skip pools with zero or invalid prices
                            if volume == 0:
                                print("Skipping pool: Zero volume")
                                continue
                                
                            if volume > max_volume:
                                max_volume = volume
                                best_pool = pool
                                print("Selected as current best pool")
                        
                        if best_pool:
                            pool_attrs = best_pool.get('attributes', {})
                            token_symbol = token_data['symbol']
                            base_symbol = pool_attrs.get('base_token_symbol', '')
                            quote_symbol = pool_attrs.get('quote_token_symbol', '')
                            
                            print(f"\nSelected pool: {base_symbol}-{quote_symbol}")
                            print(f"Token we want: {token_symbol}")
                            
                            # Determine if token is base or quote
                            is_base = token_symbol.upper() == base_symbol.upper()
                            is_quote = token_symbol.upper() == quote_symbol.upper()
                            
                            if is_base:
                                price = pool_attrs.get('base_token_price_usd', '0')
                                print(f"Token is base token, price: ${price}")
                            elif is_quote:
                                price = pool_attrs.get('quote_token_price_usd', '0')
                                print(f"Token is quote token, price: ${price}")
                            else:
                                print("WARNING: Token symbol doesn't match either side of pool!")
                                price = '0'
                            
                            price_change = pool_attrs.get('price_change_percentage', {}).get('h24', '0')
                            
                            result = {
                                **token_data,
                                'price_usd': price,
                                'price_change_24h': price_change
                            }
                            print(f"\nFinal result: {result}")
                            return result
                        else:
                            print("No best pool found despite having pools data")
                    else:
                        print("No pools data found")
                else:
                    print(f"Failed to get pools data. Status: {pools_response.status_code}")
            
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
        """Update cache for multiple tokens with staggered loading and error handling."""
        print("\n=== Updating Cached Tokens ===")
        tokens = {}
        
        # Try to load existing cache first
        cached_data = self._load_cache()
        
        for address in addresses:
            try:
                # Add delay between requests to avoid rate limits
                time.sleep(2)  # 2-second delay between requests
                
                print(f"Updating token: {address}")
                token_info = self.get_token_info(address)
                
                if token_info:
                    tokens[address] = token_info
                elif address in cached_data:
                    # If we fail to get new data, use cached data
                    print(f"Using cached data for {address}")
                    tokens[address] = cached_data[address]
                else:
                    print(f"No data available for {address}")
                    continue
                    
            except Exception as e:
                print(f"Error updating token {address}: {str(e)}")
                # Try to use cached data if update fails
                if address in cached_data:
                    print(f"Using cached data for {address} after error")
                    tokens[address] = cached_data[address]
        
        # Save successful updates to cache
        if tokens:
            self._save_cache(tokens)
        
        return tokens