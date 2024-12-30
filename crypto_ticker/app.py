from flask import Flask, render_template, request, redirect, url_for
from api.geckoterminal import GeckoTerminalAPI

app = Flask(__name__)
api = GeckoTerminalAPI()

# Store selected tokens (in memory for now)
selected_tokens = set()

@app.template_filter('float_format')
def float_format(value):
    try:
        return float(value)
    except:
        return 0.0

@app.route('/')
def home():
    tokens = api.get_token_prices()
    return render_template('dashboard.html', tokens=tokens, selected_tokens=selected_tokens)

@app.route('/add_token', methods=['POST'])
def add_token():
    token = request.form.get('token')
    if token:
        selected_tokens.add(token)
    return redirect(url_for('home'))

@app.route('/remove_token', methods=['POST'])
def remove_token():
    token = request.form.get('token')
    if token:
        selected_tokens.discard(token)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)