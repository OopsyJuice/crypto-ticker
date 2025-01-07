# LUMI Token Tracker

A web application for tracking PulseChain token prices with customizable update frequencies.

## Features

- Track up to 6 tokens simultaneously
- Customizable update frequencies:
  - High Priority: 1 token with 1-minute updates
  - Medium Priority: 2 tokens with 5-minute updates
  - Low Priority: 3 tokens with 15-minute updates
- Multiple token addition methods:
  - MetaMask wallet connection
  - Manual wallet address entry
  - Direct token address input
- Dark/Light mode support
- Real-time price and 24h change tracking

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/OopsyJuice/crypto-ticker
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

## Usage

1. Connect your MetaMask wallet or enter a wallet address to view available tokens
2. Select tokens to track and assign priority levels
3. Monitor real-time prices and 24h changes
4. Use dark/light mode toggle for preferred viewing

## Technologies Used

- Python Flask
- GeckoTerminal API
- CoinGecko API
- Web3.js
- Tailwind CSS


