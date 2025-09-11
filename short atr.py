import pandas as pd
import numpy as np
from binance.um_futures import UMFutures
import time
from typing import List, Dict, Optional

class ATRScanner:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the ATR Scanner for Binance UM Futures
        
        Args:
            api_key: Binance API key (optional for market data)
            api_secret: Binance API secret (optional for market data)
        """
        # Initialize client (no credentials needed for market data)
        self.client = UMFutures(key=api_key, secret=api_secret)
        
    def get_active_symbols(self) -> List[str]:
        """Get all active USDT perpetual futures symbols"""
        try:
            exchange_info = self.client.exchange_info()
            symbols = []
            
            for symbol_info in exchange_info['symbols']:
                # Filter for USDT perpetual futures that are trading
                if (symbol_info['symbol'].endswith('USDT') and 
                    symbol_info['contractType'] == 'PERPETUAL' and
                    symbol_info['status'] == 'TRADING'):
                    symbols.append(symbol_info['symbol'])
                    
            return symbols
        except Exception as e:
            print(f"Error getting symbols: {e}")
            return []
    
    def get_kline_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Get kline/candlestick data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (default: '1h')
            limit: Number of data points to retrieve (default: 100)
        """
        try:
            klines = self.client.klines(symbol=symbol, interval=interval, limit=limit)
            
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to appropriate data types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            return df
            
        except Exception as e:
            print(f"Error getting kline data for {symbol}: {e}")
            return None
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 21) -> float:
        """
        Calculate Average True Range (ATR)
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period (default: 21)
        """
        if len(df) < period + 1:
            return 0.0
            
        high = df['high']
        low = df['low']
        close = df['close']
        prev_close = close.shift(1)
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR as simple moving average of True Range
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else 0.0
    
    def calculate_atr_percentage(self, atr_value: float, current_price: float, multiplier: float = 1.5) -> float:
        """
        Calculate ATR as percentage of current price
        
        Args:
            atr_value: ATR value
            current_price: Current price of the asset
            multiplier: ATR multiplier (default: 1.5)
        """
        if current_price <= 0:
            return 0.0
            
        atr_adjusted = atr_value * multiplier
        atr_percentage = (atr_adjusted / current_price) * 100
        
        return atr_percentage
    
    def scan_symbols(self, min_atr_percentage: float = 0.1, atr_period: int = 50, 
                    atr_multiplier: float = 0.5, interval: str = '1m') -> List[Dict]:
        """
        Scan symbols for ATR percentage criteria
        
        Args:
            min_atr_percentage: Minimum ATR percentage threshold (default: 0.1%)
            atr_period: ATR calculation period (default: 21)
            atr_multiplier: ATR multiplier (default: 1.5)
            interval: Kline interval for analysis (default: '1h')
        """
        print("Getting active symbols...")
        symbols = self.get_active_symbols()
        print(f"Found {len(symbols)} active symbols")
        
        results = []
        
        for i, symbol in enumerate(symbols):
            try:
                print(f"Processing {symbol} ({i+1}/{len(symbols)})...")
                
                # Get kline data
                df = self.get_kline_data(symbol, interval=interval, limit=atr_period + 50)
                if df is None or len(df) < atr_period + 1:
                    continue
                
                # Calculate ATR
                atr_value = self.calculate_atr(df, period=atr_period)
                current_price = float(df['close'].iloc[-1])
                
                # Calculate ATR percentage
                atr_percentage = self.calculate_atr_percentage(atr_value, current_price, atr_multiplier)
                
                # Check if meets criteria
                if atr_percentage >= min_atr_percentage:
                    result = {
                        'symbol': symbol,
                        'current_price': current_price,
                        'atr_value': atr_value,
                        'atr_percentage': atr_percentage,
                        'atr_period': atr_period,
                        'atr_multiplier': atr_multiplier
                    }
                    results.append(result)
                    print(f" {symbol}: {atr_percentage:.3f}% ATR")
                
                # Rate limiting to avoid API limits
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        return results
    
    def display_results(self, results: List[Dict]):
        """Display scan results in a formatted table"""
        if not results:
            print("No symbols found meeting the criteria.")
            return
            
        print(f"\n{'='*80}")
        print(f"Found {len(results)} symbols with ATR% >= 0.1%")
        print(f"{'='*80}")
        print(f"{'Symbol':<15} {'Price':<12} {'ATR Value':<12} {'ATR %':<10} {'Period':<8} {'Multiplier'}")
        print(f"{'-'*80}")
        
        # Sort by ATR percentage descending
        results.sort(key=lambda x: x['atr_percentage'], reverse=True)
        
        for result in results:
            print(f"{result['symbol']:<15} "
                  f"${result['current_price']:<11.4f} "
                  f"{result['atr_value']:<12.6f} "
                  f"{result['atr_percentage']:<9.3f}% "
                  f"{result['atr_period']:<8} "
                  f"{result['atr_multiplier']}")

    def save_results_to_txt(self, results: List[Dict], filename: str = None):
        """Save results to text file in Binance format"""
        if not results:
            print("No results to save.")
            return
            
        if filename is None:
            filename = f"atr_scan_results_{int(time.time())}.txt"
        
        # Sort by ATR percentage descending
        results.sort(key=lambda x: x['atr_percentage'], reverse=True)
        
        # Create list of symbols in BINANCE:SYMBOL.P format
        symbol_list = []
        for result in results:
            symbol = result['symbol']
            binance_format = f"BINANCE:{symbol}.P"
            symbol_list.append(binance_format)
        
        # Join all symbols with commas (no spaces after commas to match your format)
        symbols_string = ','.join(symbol_list)
        
        # Write to file
        try:
            with open(filename, 'w') as f:
                f.write(symbols_string)
            print(f"\nResults saved to {filename}")
            print(f"Total symbols saved: {len(symbol_list)}")
        except Exception as e:
            print(f"Error saving to file: {e}")

def main():
    """Main function to run the ATR scanner"""
    print("Binance UM Futures ATR Scanner")
    print("="*50)
    
    # Initialize scanner (no API credentials needed for market data)
    scanner = ATRScanner()
    
    # Scan for symbols with ATR% > 0.1%
    results = scanner.scan_symbols(
        min_atr_percentage=0.2,  # 0.2% threshold
        atr_period=50,           # 50-period ATR
        atr_multiplier=0.5,      # 0.5x multiplier
        interval='1m'            # 1-minute intervals
    )
    
    # Display results
    scanner.display_results(results)
    
    # Save results to TXT file if any found
    if results:
        scanner.save_results_to_txt(results)

if __name__ == "__main__":
    main()