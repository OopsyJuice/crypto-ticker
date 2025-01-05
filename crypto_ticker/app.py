from flask import Flask, render_template, jsonify, request, redirect, url_for
from api.geckoterminal import GeckoTerminalAPI
import threading
import time
import re
import requests

app = Flask(__name__)
api = GeckoTerminalAPI()

# Cache for tokens
token_cache = {
    'data': {},
    'last_update': 0,
    'updating': False
}

# Store selected tokens
selected_tokens = set()

def update_cache():
    print("Cache update thread started")
    while True:
        print("\n--- Cache Update Cycle ---")
        if not token_cache['updating'] and selected_tokens:
            token_cache['updating'] = True
            try:
                print(f"Updating cache for tokens: {selected_tokens}")
                
                # Update regular tokens
                new_data = api.update_cached_tokens(list(selected_tokens))
                print(f"New data from API: {new_data}")
                token_cache['data'].update(new_data)
                
                # Debug PLS specific updates
                if 'native' in selected_tokens:
                    print("Found native PLS in selected tokens")
                    try:
                        # Try to get WPLS price directly from api.get_token_info
                        wpls_info = api.get_token_info('0xa1077a294dde1b09bb078844df4D16dB296f254A')
                        print(f"WPLS info received: {wpls_info}")
                        
                        if wpls_info and wpls_info.get('price_usd'):
                            print("Updating PLS price with WPLS data")
                            token_cache['data']['native'] = {
                                'address': 'native',
                                'symbol': 'PLS',
                                'name': 'Pulse',
                                'price_usd': wpls_info['price_usd'],
                                'price_change_24h': wpls_info.get('price_change_24h', '0')
                            }
                            print(f"Updated native token data: {token_cache['data']['native']}")
                    except Exception as e:
                        print(f"Error updating PLS price: {e}")
                
                print(f"Final cache state: {token_cache['data']}")
                token_cache['last_update'] = time.time()
            finally:
                token_cache['updating'] = False
        time.sleep(10)

update_thread = threading.Thread(target=update_cache, daemon=True)
update_thread.start()

@app.template_filter('float_format')
def float_format(value):
    try:
        return float(value)
    except:
        return 0.0

@app.route('/')
def home():
    if selected_tokens and not token_cache['data']:
        token_cache['data'] = api.update_cached_tokens(list(selected_tokens))
        token_cache['last_update'] = time.time()
    
    last_update = time.strftime('%I:%M:%S %p', time.localtime(token_cache['last_update']))
    return render_template('dashboard.html',
                         tokens=token_cache['data'],
                         selected_tokens=selected_tokens,
                         last_update=last_update)

@app.route('/api/tokens/<address>')
def get_wallet_tokens(address):
    try:
        print(f"\nFetching tokens for address: {address}")
        url = 'https://api.scan.pulsechain.com/api'

        # First get native PLS balance
        pls_params = {
            'module': 'account',
            'action': 'balance',
            'address': address
        }
        
        # Get token list first
        list_params = {
            'module': 'account',
            'action': 'tokenlist',
            'address': address
        }
        
        # Make requests
        pls_response = requests.get(url, params=pls_params)
        token_list_response = requests.get(url, params=list_params)
        
        tokens = []
        
        # Add PLS if there's a balance
        if pls_response.ok:
            pls_data = pls_response.json()
            pls_balance = pls_data.get('result', '0')
            if int(pls_balance) > 0:
                tokens.append({
                    'symbol': 'PLS',
                    'contractAddress': 'native',
                    'name': 'Pulse',
                    'decimals': '18'
                })

        # Add tokens with current balances
        if token_list_response.ok:
            data = token_list_response.json()
            token_list = data.get('result', [])
            
            for token in token_list:
                # Only add tokens with balance > 0
                if float(token.get('balance', 0)) > 0:
                    tokens.append({
                        'symbol': token.get('symbol'),
                        'contractAddress': token.get('contractAddress'),
                        'name': token.get('name'),
                        'decimals': token.get('decimals')
                    })

        return jsonify(tokens)
            
    except Exception as e:
        print(f"Error getting wallet tokens: {str(e)}")
        return jsonify([])

@app.route('/api/token/<address>')
def get_single_token_info(address):
    try:
        token_info = api.get_token_info(address)
        if token_info:
            return jsonify(token_info)
        return jsonify(None)
    except Exception as e:
        print(f"Error getting token info: {str(e)}")
        return jsonify(None)

@app.route('/add_token', methods=['POST'])
def add_token():
    try:
        if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            address = request.form.get('token_address', '').lower()
        else:
            data = request.get_json()
            address = data.get('token_address', '').lower()

        print(f"\n=== Adding Token: {address} ===")
        print(f"Current token count: {len(selected_tokens)}")
        print(f"Current selected tokens: {selected_tokens}")

        # Check if token is already selected
        if address in selected_tokens:
            print(f"Token {address} is already selected")
            return redirect(url_for('home'))

        # Pre-check the limit
        if len(selected_tokens) >= 6:
            print("Token limit already reached")
            return redirect(url_for('home'))

        if address:
            print("Creating GeckoTerminal API instance...")
            gecko_api = GeckoTerminalAPI()
            
            print(f"Fetching token info for {address}...")
            token_info = gecko_api.get_token_info(address)
            
            print(f"Token info received: {token_info}")
            
            if token_info:
                # Double-check limit before adding
                if len(selected_tokens) < 6:
                    print("Adding token to selected tokens and cache...")
                    selected_tokens.add(address)
                    token_cache['data'][address] = token_info
                    
                    print("After adding token:")
                    print(f"Selected tokens: {selected_tokens}")
                    print(f"Token count: {len(selected_tokens)}")
                    print(f"Token cache: {token_cache['data'][address]}")
                else:
                    print("Token limit reached during processing")
            else:
                print(f"Failed to get token info for {address}")
                
        return redirect(url_for('home'))
        
    except Exception as e:
        print(f"Error in add_token route: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return redirect(url_for('home'))
            

@app.route('/remove_token', methods=['POST'])
def remove_token():
    address = request.form.get('token_address')
    if address:
        selected_tokens.discard(address)
        token_cache['data'].pop(address, None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)