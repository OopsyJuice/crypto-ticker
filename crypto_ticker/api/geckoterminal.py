import requests
from typing import Dict, List, Optional

class GeckoTerminalAPI:
    BASE_URL = "https://api.geckoterminal.com/api/v2"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_token_prices(self) -> List[Dict]:
        try:
            response = self.session.get(f"{self.BASE_URL}/networks/pulsechain/pools")
            data = response.json()
            
            token_prices = {}
            
            for pool in data.get('data', []):
                attrs = pool.get('attributes', {})
                name = attrs.get('name', '')
                if '/' not in name:
                    continue
                    
                token_symbol = name.split('/')[0].strip()
                price_usd = attrs.get('base_token_price_usd')
                volume = attrs.get('volume_usd', {}).get('h24', '0')
                price_change = attrs.get('price_change_percentage', {}).get('h24', '0')
                
                try:
                    volume = float(volume or 0)
                    if not token_prices.get(token_symbol) or volume > token_prices[token_symbol]['volume_24h']:
                        token_prices[token_symbol] = {
                            'symbol': token_symbol,
                            'price_usd': price_usd,
                            'price_change_24h': price_change,
                            'volume_24h': volume
                        }
                except ValueError:
                    continue
                    
            return sorted(token_prices.values(), key=lambda x: x.get('volume_24h', 0), reverse=True)
            
        except Exception as e:
            print(f"Error: {e}")
            return []