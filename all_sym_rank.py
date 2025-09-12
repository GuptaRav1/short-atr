from binance.um_futures import UMFutures
import pandas as pd
from datetime import datetime

def get_top_100_um_futures():
    """
    Fetch top 100 UM futures trading pairs from Binance
    Sorted by 24hr volume in descending order
    """
    
    # Initialize UM Futures client (no API key needed for public data)
    client = UMFutures()
    
    try:
        # Get 24hr ticker statistics for all symbols
        print("Fetching 24hr ticker statistics...")
        ticker_stats = client.ticker_24hr_price_change()
        
        # Filter for USDT perpetual futures (UM futures)
        usdt_futures = []
        for ticker in ticker_stats:
            symbol = ticker['symbol']
            # Filter for USDT perpetual futures (exclude quarterly futures)
            if symbol.endswith('USDT') and not any(month in symbol for month in ['0325', '0626', '0927', '1228']):
                usdt_futures.append({
                    'symbol': symbol,
                    'baseAsset': symbol.replace('USDT', ''),
                    'lastPrice': float(ticker['lastPrice']),
                    'priceChange': float(ticker['priceChange']),
                    'priceChangePercent': float(ticker['priceChangePercent']),
                    'volume': float(ticker['volume']),
                    'quoteVolume': float(ticker['quoteVolume']),
                    'count': int(ticker['count']),
                    'openPrice': float(ticker['openPrice']),
                    'highPrice': float(ticker['highPrice']),
                    'lowPrice': float(ticker['lowPrice'])
                })
        
        # Sort by 24hr quote volume (USDT volume) in descending order
        usdt_futures_sorted = sorted(usdt_futures, key=lambda x: x['quoteVolume'], reverse=True)
        
        # Get top 100
        top_100 = usdt_futures_sorted[:100]
        
        # Create DataFrame for better display
        df = pd.DataFrame(top_100)
        
        # Format numbers for better readability
        df['lastPrice'] = df['lastPrice'].apply(lambda x: f"{x:.6f}".rstrip('0').rstrip('.'))
        df['priceChangePercent'] = df['priceChangePercent'].apply(lambda x: f"{x:.2f}%")
        df['quoteVolume'] = df['quoteVolume'].apply(lambda x: f"{x:,.0f}")
        df['volume'] = df['volume'].apply(lambda x: f"{x:,.0f}")
        
        print(f"\n{'='*80}")
        print(f"TOP 100 UM FUTURES COINS BY 24HR VOLUME")
        print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*80}")
        
        # Display results
        for i, coin in enumerate(top_100, 1):
            print(f"{i:2d}. {coin['baseAsset']:<12} | "
                  f"Price: ${coin['lastPrice']:<12} | "
                  f"Change: {df.iloc[i-1]['priceChangePercent']:>8} | "
                  f"Volume: ${df.iloc[i-1]['quoteVolume']:>15}")
        
        print(f"\n{'='*80}")
        
        # Return the list of base assets for further use
        top_100_symbols = [coin['baseAsset'] for coin in top_100]
        
        return top_100_symbols
        
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

def get_exchange_info():
    """
    Get additional exchange information for UM futures
    """
    client = UMFutures()
    
    try:
        exchange_info = client.exchange_info()
        active_symbols = []
        
        for symbol_info in exchange_info['symbols']:
            if symbol_info['status'] == 'TRADING' and symbol_info['symbol'].endswith('USDT'):
                active_symbols.append({
                    'symbol': symbol_info['symbol'],
                    'baseAsset': symbol_info['baseAsset'],
                    'quoteAsset': symbol_info['quoteAsset'],
                    'contractType': symbol_info['contractType'],
                    'status': symbol_info['status']
                })
        
        print(f"\nTotal active UM futures symbols: {len(active_symbols)}")
        return active_symbols
        
    except Exception as e:
        print(f"Error fetching exchange info: {str(e)}")
        return None

if __name__ == "__main__":
    # Get top 100 UM futures coins
    top_100 = get_top_100_um_futures()
    