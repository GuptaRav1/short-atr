import pandas as pd
import numpy as np
from binance.um_futures import UMFutures
import time
from typing import List, Dict, Optional

client = UMFutures()

def save_symbols_to_file(symbols: List[str], filename: str = "binance_symbols.txt"):
    """Save symbols in TradingView format to a text file"""
    try:
        # Convert symbols to TradingView format (BINANCE:SYMBOL.P)
        tradingview_symbols = [f"BINANCE:{symbol}.P" for symbol in symbols]
        
        # Join all symbols with commas
        symbols_string = ",".join(tradingview_symbols)
        
        # Write to file
        with open(filename, 'w') as file:
            file.write(symbols_string)
        
        print(f"Successfully saved {len(symbols)} symbols to {filename}")
        print(f"First few symbols: {','.join(tradingview_symbols[:5])}...")
        
    except Exception as e:
        print(f"Error saving symbols to file: {e}")

def get_symbol_rankings() -> Dict[str, float]:
    """Get 24hr ticker statistics for ranking symbols by volume"""
    try:
        ticker_24hr = client.ticker_24hr_price_change()
        rankings = {}
        
        for ticker in ticker_24hr:
            symbol = ticker['symbol']
            # Use quote volume (USDT volume) for ranking
            quote_volume = float(ticker['quoteVolume'])
            rankings[symbol] = quote_volume
            
        return rankings
    except Exception as e:
        print(f"Error getting ticker data: {e}")
        return {}

def get_active_symbols_ranked() -> List[str]:
    """Get all active USDT perpetual futures symbols sorted by ranking and save to file"""
    try:
        # Get exchange info
        exchange_info = client.exchange_info()
        active_symbols = []
        
        for symbol_info in exchange_info['symbols']:
            # Filter for USDT perpetual futures that are trading
            if (symbol_info['symbol'].endswith('USDT') and 
                symbol_info['contractType'] == 'PERPETUAL' and
                symbol_info['status'] == 'TRADING'):
                active_symbols.append(symbol_info['symbol'])
        
        print(f"Found {len(active_symbols)} active USDT perpetual futures")
        
        # Get ranking data (24hr volume)
        print("Fetching ranking data...")
        rankings = get_symbol_rankings()
        
        # Sort symbols by volume (descending order - highest volume first)
        ranked_symbols = sorted(active_symbols, 
                               key=lambda x: rankings.get(x, 0), 
                               reverse=True)
        
        # Print top 10 symbols with their volumes
        print("\nTop 10 symbols by 24hr volume:")
        for i, symbol in enumerate(ranked_symbols[:10], 1):
            volume = rankings.get(symbol, 0)
            print(f"{i:2d}. {symbol:15s} - ${volume:,.0f} USDT")
        
        # Save to file
        save_symbols_to_file(ranked_symbols)
        
        return ranked_symbols
        
    except Exception as e:
        print(f"Error getting ranked symbols: {e}")
        return []

def get_active_symbols() -> List[str]:
    """Legacy function - now calls the ranked version"""
    return get_active_symbols_ranked()

# Run the function
if __name__ == "__main__":
    ranked_symbols = get_active_symbols_ranked()