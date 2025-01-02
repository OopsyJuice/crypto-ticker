from flask import Flask, render_template, jsonify, request, redirect, url_for
from api.geckoterminal import GeckoTerminalAPI
import threading
import time
import re

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
    while True:
        if not token_cache['updating'] and selected_tokens:
            token_cache['updating'] = True
            try:
                new_data = api.update_cached_tokens(list(selected_tokens))
                token_cache['data'].update(new_data)
                token_cache['last_update'] = time.time()
            finally:
                token_cache['updating'] = False
        time.sleep(60)

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

@app.route('/add_token', methods=['POST'])
def add_token():
    address = request.form.get('token_address', '').lower()
    if address and len(selected_tokens) < 6:
        if re.match(r'^0x[a-fA-F0-9]{40}$', address):
            token_info = api.get_token_info(address)
            if token_info:
                selected_tokens.add(address)
                token_cache['data'][address] = token_info
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