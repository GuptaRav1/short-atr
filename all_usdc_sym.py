from binance.um_futures import UMFutures
from typing import List, Dict

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
        print(f"First few symbols: {','.join(tradingview_symbols[:5])}...")
        
    except Exception as e:
        print(f"Error saving symbols to file: {e}")

def get_active_usdc_symbols() -> List[str]:
    """Get all active USDC perpetual futures symbols and save to file"""
    try:
        exchange_info = client.exchange_info()
        symbols = []
        
        for symbol_info in exchange_info['symbols']:
            # Filter for USDC perpetual futures that are trading
            if (symbol_info['symbol'].endswith('USDC') and 
                symbol_info['contractType'] == 'PERPETUAL' and
                symbol_info['status'] == 'TRADING'):
                symbols.append(symbol_info['symbol'])
        
        # Sort symbols alphabetically
        symbols.sort()
        
        # Convert to TradingView format and save to file
        save_symbols_to_file(symbols)
        
        print(f"Found {len(symbols)} active USDC perpetual futures:")
        for symbol in symbols:
            print(f"  {symbol}")
        
        return symbols
    except Exception as e:
        print(f"Error getting USDC symbols: {e}")
        return []

def get_both_usdt_and_usdc_symbols() -> Dict[str, List[str]]:
    """Get both USDT and USDC perpetual futures symbols"""
    try:
        exchange_info = client.exchange_info()
        usdt_symbols = []
        usdc_symbols = []
        
        for symbol_info in exchange_info['symbols']:
            if (symbol_info['contractType'] == 'PERPETUAL' and
                symbol_info['status'] == 'TRADING'):
                
                if symbol_info['symbol'].endswith('USDT'):
                    usdt_symbols.append(symbol_info['symbol'])
                elif symbol_info['symbol'].endswith('USDC'):
                    usdc_symbols.append(symbol_info['symbol'])
        
        # Sort both lists
        usdt_symbols.sort()
        usdc_symbols.sort()
        
        # Save USDC symbols
        save_symbols_to_file(usdc_symbols, "binance_usdc_symbols.txt")
        
        # Save USDT symbols
        save_symbols_to_file(usdt_symbols, "binance_usdt_symbols.txt")
        
        print(f"\nSummary:")
        print(f"USDT perpetual futures: {len(usdt_symbols)}")
        print(f"USDC perpetual futures: {len(usdc_symbols)}")
        
        return {
            'USDT': usdt_symbols,
            'USDC': usdc_symbols
        }
    except Exception as e:
        print(f"Error getting symbols: {e}")
        return {'USDT': [], 'USDC': []}

# Get USDC symbols only
print("Getting USDC perpetual futures symbols...")
usdc_symbols = get_active_usdc_symbols()

# Uncomment the line below if you want both USDT and USDC symbols
# all_symbols = get_both_usdt_and_usdc_symbols()