import json
import requests
import os
from dotenv import load_dotenv
import time
import re

def fetch_and_format_token_details(token_code):
    api_key = os.getenv('API_KEY')
    url = "https://api.livecoinwatch.com/coins/single"
    
    headers = {
        "content-type": "application/json",
        "x-api-key": api_key
    }
    
    payload = {
        "currency": "USD",
        "code": token_code,
        "meta": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            
            # Format for livecoinwatch.py structure
            formatted_output = {
                # We'll need to get the contract address from somewhere
                "'CONTRACT_ADDRESS'": {
                    'symbol': token_code.replace('_', ''),  # Remove underscores for symbol
                    'name': data.get('name', ''),
                    'code': token_code,  # Keep original code with underscores
                    'platform': 'PULSECHAIN'
                }
            }
            
            """print(f"\nFormatted output for {token_code}:")"""
            print(json.dumps(formatted_output, indent=4))
            return formatted_output
            
        else:
            print(f"Error fetching {token_code}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception fetching {token_code}: {str(e)}")
        return None

def parse_output_file():
    with open('get_pulsechain_tokens_output.txt', 'r') as file:
        content = file.readlines()
    
    token_codes = []
    for line in content:
        if line.startswith('Matched token:'):
            code = line.strip().split('(')[-1].rstrip(')\n')
            token_codes.append(code)
    
    print(f"Found {len(token_codes)} token codes")
    
    all_tokens = {}
    for token_code in token_codes:
        """print(f"\nProcessing {token_code}...")"""
        result = fetch_and_format_token_details(token_code)
        if result:
            all_tokens.update(result)
        time.sleep(1)
    
    # Final output in desired format
    print("\nFinal token_mapping format:")
    print("token_mapping = {")
    for contract, details in all_tokens.items():
        print(f"    {contract}: {{")
        print(f"        'symbol': '{details['symbol']}',")
        print(f"        'name': '{details['name']}',")
        print(f"        'code': '{details['code']}',")
        print(f"        'platform': '{details['platform']}'")
        print("    },")
    print("}")

if __name__ == "__main__":
    load_dotenv()
    parse_output_file()