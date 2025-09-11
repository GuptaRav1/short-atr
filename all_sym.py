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




def get_active_symbols() -> List[str]:
    """Get all active USDT perpetual futures symbols and save to file"""
    try:
        exchange_info = client.exchange_info()
        symbols = []
        
        for symbol_info in exchange_info['symbols']:
            # Filter for USDT perpetual futures that are trading
            if (symbol_info['symbol'].endswith('USDT') and 
                symbol_info['contractType'] == 'PERPETUAL' and
                symbol_info['status'] == 'TRADING'):
                symbols.append(symbol_info['symbol'])
        
        # Convert to TradingView format and save to file
        save_symbols_to_file(symbols)
        
        return symbols
    except Exception as e:
        print(f"Error getting symbols: {e}")
        return []



get_active_symbols()