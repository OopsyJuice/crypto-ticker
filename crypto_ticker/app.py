from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from api.livecoinwatch import LiveCoinWatchClient
import threading
import time
import re
import requests

app = Flask(__name__, static_url_path='/static', static_folder='static')
api = LiveCoinWatchClient()

# Cache for tokens
token_cache = {
    'data': {},
    'last_updates': {},  # Track individual token update times
    'last_update': 0,
    'updating': False
}

# Track token priorities
token_priorities = {
    'high': set(),    # 1 minute updates
    'medium': set(),  # 5 minute updates
    'low': set()      # 15 minute updates
}

# Store selected tokens
selected_tokens = set()

def update_cache():
    print("Cache update thread started")
    while True:
        print("\n--- Cache Update Cycle ---")
        current_time = time.time()
        
        if not token_cache['updating']:
            token_cache['updating'] = True
            try:
                # Update high priority tokens (1 minute updates)
                for address in token_priorities['high']:
                    last_update = token_cache.get('last_updates', {}).get(address, 0)
                    if current_time - last_update >= 60:  # 1 minute
                        print(f"Updating high priority token: {address}")
                        token_info = api.get_token_info(address)
                        if token_info:
                            token_cache['data'][address] = token_info
                            if 'last_updates' not in token_cache:
                                token_cache['last_updates'] = {}
                            token_cache['last_updates'][address] = current_time

                # Update medium priority tokens (5 minutes)
                for address in token_priorities['medium']:
                    last_update = token_cache.get('last_updates', {}).get(address, 0)
                    if current_time - last_update >= 300:  # 5 minutes
                        print(f"Updating medium priority token: {address}")
                        token_info = api.get_token_info(address)
                        if token_info:
                            token_cache['data'][address] = token_info
                            if 'last_updates' not in token_cache:
                                token_cache['last_updates'] = {}
                            token_cache['last_updates'][address] = current_time

                # Update low priority tokens (15 minutes)
                for address in token_priorities['low']:
                    last_update = token_cache.get('last_updates', {}).get(address, 0)
                    if current_time - last_update >= 900:  # 15 minutes
                        print(f"Updating low priority token: {address}")
                        token_info = api.get_token_info(address)
                        if token_info:
                            token_cache['data'][address] = token_info
                            if 'last_updates' not in token_cache:
                                token_cache['last_updates'] = {}
                            token_cache['last_updates'][address] = current_time

                token_cache['last_update'] = current_time
                
            finally:
                token_cache['updating'] = False
                
        time.sleep(10)  # Check every 10 seconds for tokens that need updates

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
                         token_priorities=token_priorities,
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
            print(f"PLS response: {pls_data}")  # Debug line
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
            print(f"Token list response: {data}")  # Debug line
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

        print(f"Final tokens list: {tokens}")  # Debug line
        return jsonify(tokens)
            
    except Exception as e:
        print(f"Error getting wallet tokens: {str(e)}")
        return jsonify([])

@app.route('/api/token/<address>')
def get_single_token_info(address):
    try:
        print(f"Fetching token info for address: {address}")
        token_info = api.get_token_info(address)
        print(f"Token info received: {token_info}")
        if token_info:
            print("Returning token info:")
            print(token_info)
            return jsonify(token_info)
        else:
            print("Token info not found")
            return jsonify(None)
    except Exception as e:
        print(f"Error getting token info: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify(None)

@app.route('/add_token', methods=['POST'])
def add_token():
    try:
        data = request.get_json() if request.is_json else request.form
        address = data.get('token_address', '').lower()
        priority = data.get('priority', 'low')

        print(f"\n=== Adding Token: {address} ===")
        print(f"Priority Level: {priority}")
        print(f"Current priorities: {token_priorities}")

        # Check priority limits
        if priority == 'high' and len(token_priorities['high']) >= 1:
            print(f"High priority tokens: {token_priorities['high']}")
            return jsonify({'error': 'High priority limit reached (max 1)'}), 400
        elif priority == 'medium' and len(token_priorities['medium']) >= 2:
            return jsonify({'error': 'Medium priority limit reached (max 2)'}), 400
        elif priority == 'low' and len(token_priorities['low']) >= 3:
            return jsonify({'error': 'Low priority limit reached (max 3)'}), 400

        # Get token info
        if address:
            token_info = api.get_token_info(address)
            if token_info:
                # Add to selected tokens and appropriate priority set
                selected_tokens.add(address)
                
                # Remove from any existing priority sets
                for p in token_priorities:
                    token_priorities[p].discard(address)
                    
                # Add to new priority set
                token_priorities[priority].add(address)
                
                # Update cache
                token_cache['data'][address] = token_info
                
                print(f"Token added with priority {priority}")
                print(f"Current priorities: {token_priorities}")
                return jsonify({'success': True})
            else:
                print(f"Failed to get token info for {address}")
                
        return jsonify({'error': 'Invalid token'}), 400
        
    except Exception as e:
        print(f"Error in add_token route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/remove_token', methods=['POST'])
def remove_token():
    address = request.form.get('token_address')
    if address:
        selected_tokens.discard(address)
        token_cache['data'].pop(address, None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)