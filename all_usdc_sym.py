# pip install binance-futures-connector

from binance.um_futures import UMFutures
from typing import List, Dict, Tuple

client = UMFutures()

def save_symbols_to_file(symbols: List[str], filename: str = "binance_usdc_symbols.txt"):
    """Save symbols in TradingView format to a text file"""
    try:
        # Convert symbols to TradingView format (BINANCE:SYMBOL.P)
        tradingview_symbols = [f"BINANCE:{symbol}.P" for symbol in symbols]
        
        # Join all symbols with commas
        symbols_string = ",".join(tradingview_symbols)
        
        # Write to file
        with open(filename, 'w') as file:
            file.write(symbols_string)
        
        print(f"Successfully saved {len(symbols)} USDC symbols to {filename}")
        print(f"First few symbols (by volume): {','.join(tradingview_symbols[:5])}...")
        
    except Exception as e:
        print(f"Error saving symbols to file: {e}")

def get_active_usdc_symbols() -> List[str]:
    """Get all active USDC perpetual futures symbols sorted by volume and save to file"""
    try:
        # Get exchange info for symbol filtering
        exchange_info = client.exchange_info()
        valid_symbols = set()
        
        for symbol_info in exchange_info['symbols']:
            # Filter for USDC perpetual futures that are trading
            if (symbol_info['symbol'].endswith('USDC') and 
                symbol_info['contractType'] == 'PERPETUAL' and
                symbol_info['status'] == 'TRADING'):
                valid_symbols.add(symbol_info['symbol'])
        
        # Get 24hr ticker data for all symbols
        tickers = client.ticker_24hr_price_change()
        
        # Create list of (symbol, volume) tuples for USDC symbols
        symbol_volumes: List[Tuple[str, float]] = []
        
        for ticker in tickers:
            symbol = ticker['symbol']
            if symbol in valid_symbols:
                # Use quote volume (volume in USDC) for better comparison
                volume = float(ticker['quoteVolume'])
                symbol_volumes.append((symbol, volume))
        
        # Sort by volume (descending)
        symbol_volumes.sort(key=lambda x: x[1], reverse=True)
        
        # Extract just the symbols
        sorted_symbols = [symbol for symbol, volume in symbol_volumes]
        
        # Save to file
        save_symbols_to_file(sorted_symbols)
        
        print(f"\nFound {len(sorted_symbols)} active USDC perpetual futures (sorted by 24h volume):")
        print("\nTop 10 by volume:")
        for i, (symbol, volume) in enumerate(symbol_volumes[:10], 1):
            print(f"  {i}. {symbol}: ${volume:,.0f}")
        
        return sorted_symbols
    except Exception as e:
        print(f"Error getting USDC symbols: {e}")
        return []

# Get USDC symbols sorted by volume
print("Getting USDC perpetual futures symbols sorted by volume...")
usdc_symbols = get_active_usdc_symbols()