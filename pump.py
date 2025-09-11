#!/usr/bin/env python3
"""
Crypto Pump Detector using Binance Futures Connector
Finds recently pumped coins based on price movement analysis
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd

from binance.um_futures import UMFutures
from binance.error import ClientError


class CryptoPumpDetector:
    def __init__(self, api_key: str = None, api_secret: str = None):
        """Initialize the pump detector with optional API credentials"""
        self.client = UMFutures(key=api_key, secret=api_secret)
        self.excluded_symbols = {'USDCUSDT', 'TUSDUSDT', 'BUSDUSDT', 'FDUSDUSDT'}  # Exclude stablecoins
    
    def get_all_futures_symbols(self) -> List[str]:
        """Get all active USDT futures trading pairs"""
        try:
            exchange_info = self.client.exchange_info()
            symbols = []
            
            for symbol_info in exchange_info['symbols']:
                symbol = symbol_info['symbol']
                if (symbol.endswith('USDT') and 
                    symbol_info['status'] == 'TRADING' and
                    symbol not in self.excluded_symbols):
                    symbols.append(symbol)
            
            return sorted(symbols)
        except ClientError as e:
            print(f"Error fetching symbols: {e}")
            return []
    
    def get_24h_ticker_stats(self) -> Dict[str, Dict]:
        """Get 24h ticker statistics for all symbols"""
        try:
            ticker_data = self.client.ticker_24hr_price_change()
            ticker_dict = {}
            
            for ticker in ticker_data:
                symbol = ticker['symbol']
                if symbol.endswith('USDT') and symbol not in self.excluded_symbols:
                    ticker_dict[symbol] = {
                        'symbol': symbol,
                        'price_change_percent': float(ticker['priceChangePercent']),
                        'volume': float(ticker['volume']),
                        'quote_volume': float(ticker['quoteVolume']),
                        'count': int(ticker['count']),
                        'last_price': float(ticker['lastPrice']),
                        'high_price': float(ticker['highPrice']),
                        'low_price': float(ticker['lowPrice']),
                        'open_price': float(ticker['openPrice'])
                    }
            
            return ticker_dict
        except ClientError as e:
            print(f"Error fetching 24h ticker data: {e}")
            return {}
    
    def get_kline_data(self, symbol: str, interval: str = '1h', limit: int = 24) -> List[Dict]:
        """Get kline/candlestick data for a symbol"""
        try:
            klines = self.client.klines(symbol=symbol, interval=interval, limit=limit)
            processed_klines = []
            
            for kline in klines:
                processed_klines.append({
                    'open_time': datetime.fromtimestamp(kline[0] / 1000),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'quote_volume': float(kline[7])
                })
            
            return processed_klines
        except ClientError as e:
            print(f"Error fetching kline data for {symbol}: {e}")
            return []
    
    def calculate_pump_metrics(self, symbol: str, ticker_data: Dict) -> Dict:
        """Calculate various pump detection metrics for a symbol"""
        metrics = {
            'symbol': symbol,
            'current_price': ticker_data['last_price'],
            'price_change_24h': ticker_data['price_change_percent'],
            'volume_24h': ticker_data['volume'],
            'quote_volume_24h': ticker_data['quote_volume'],
            'trade_count_24h': ticker_data['count'],
            'high_24h': ticker_data['high_price'],
            'low_24h': ticker_data['low_price']
        }
        
        # Calculate additional metrics
        metrics['price_range_24h'] = ((ticker_data['high_price'] - ticker_data['low_price']) / ticker_data['low_price']) * 100
        metrics['distance_from_high'] = ((ticker_data['high_price'] - ticker_data['last_price']) / ticker_data['high_price']) * 100
        metrics['avg_trade_size'] = ticker_data['quote_volume'] / ticker_data['count'] if ticker_data['count'] > 0 else 0
        
        # Get hourly data for more detailed analysis
        kline_data = self.get_kline_data(symbol, '1h', 24)
        if kline_data:
            # Calculate hourly volatility
            hourly_changes = []
            for i in range(1, len(kline_data)):
                change = ((kline_data[i]['close'] - kline_data[i-1]['close']) / kline_data[i-1]['close']) * 100
                hourly_changes.append(abs(change))
            
            metrics['avg_hourly_volatility'] = sum(hourly_changes) / len(hourly_changes) if hourly_changes else 0
            
            # Find the biggest single hour pump
            max_hourly_pump = 0
            for i in range(1, len(kline_data)):
                hourly_pump = ((kline_data[i]['high'] - kline_data[i-1]['close']) / kline_data[i-1]['close']) * 100
                max_hourly_pump = max(max_hourly_pump, hourly_pump)
            
            metrics['max_hourly_pump'] = max_hourly_pump
            
            # Volume spike detection (compare last 6 hours to previous 18)
            if len(kline_data) >= 24:
                recent_volume = sum(k['volume'] for k in kline_data[-6:])
                previous_volume = sum(k['volume'] for k in kline_data[-24:-6])
                metrics['volume_spike_ratio'] = recent_volume / (previous_volume / 3) if previous_volume > 0 else 0
            else:
                metrics['volume_spike_ratio'] = 0
        
        return metrics
    
    def calculate_pump_score(self, metrics: Dict) -> float:
        """Calculate a composite pump score based on various metrics"""
        score = 0
        
        # Price change weight (0-40 points)
        price_change = metrics['price_change_24h']
        if price_change > 50:
            score += 40
        elif price_change > 30:
            score += 30
        elif price_change > 15:
            score += 20
        elif price_change > 5:
            score += 10
        
        # Volume spike weight (0-25 points)
        volume_spike = metrics.get('volume_spike_ratio', 0)
        if volume_spike > 5:
            score += 25
        elif volume_spike > 3:
            score += 20
        elif volume_spike > 2:
            score += 15
        elif volume_spike > 1.5:
            score += 10
        
        # Max hourly pump weight (0-20 points)
        max_pump = metrics.get('max_hourly_pump', 0)
        if max_pump > 20:
            score += 20
        elif max_pump > 15:
            score += 15
        elif max_pump > 10:
            score += 10
        elif max_pump > 5:
            score += 5
        
        # Distance from high (penalty for coins that already dumped)
        distance = metrics.get('distance_from_high', 0)
        if distance > 30:
            score *= 0.5  # Heavy penalty
        elif distance > 20:
            score *= 0.7
        elif distance > 10:
            score *= 0.85
        
        # Minimum volume filter
        if metrics['quote_volume_24h'] < 1000000:  # Less than 1M USDT volume
            score *= 0.5
        
        return round(score, 2)
    
    def find_pumped_coins(self, min_pump_score: float = 30, top_n: int = 20) -> List[Dict]:
        """Find coins that show signs of recent pumping"""
        print("Fetching 24h ticker data...")
        ticker_data = self.get_24h_ticker_stats()
        
        if not ticker_data:
            print("No ticker data available")
            return []
        
        print(f"Analyzing {len(ticker_data)} symbols...")
        pumped_coins = []
        
        # Filter for coins with significant positive movement first
        potential_pumps = {k: v for k, v in ticker_data.items() if v['price_change_percent'] > 5}
        
        print(f"Found {len(potential_pumps)} coins with >5% gains, analyzing in detail...")
        
        for i, (symbol, data) in enumerate(potential_pumps.items(), 1):
            if i % 50 == 0:
                print(f"Processed {i}/{len(potential_pumps)} symbols...")
            
            try:
                metrics = self.calculate_pump_metrics(symbol, data)
                pump_score = self.calculate_pump_score(metrics)
                
                if pump_score >= min_pump_score:
                    metrics['pump_score'] = pump_score
                    pumped_coins.append(metrics)
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue
        
        # Sort by pump score descending
        pumped_coins.sort(key=lambda x: x['pump_score'], reverse=True)
        
        return pumped_coins[:top_n]
    
    def print_results(self, pumped_coins: List[Dict]):
        """Print formatted results"""
        if not pumped_coins:
            print("\nNo significantly pumped coins found.")
            return
        
        print(f"\n🚀 TOP PUMPED COINS (Found {len(pumped_coins)} candidates)")
        print("=" * 120)
        print(f"{'Rank':<4} {'Symbol':<15} {'Score':<6} {'24h %':<8} {'Price':<12} {'Vol(USDT)':<12} {'Max Hr %':<9} {'From High %':<11}")
        print("-" * 120)
        
        for i, coin in enumerate(pumped_coins, 1):
            print(f"{i:<4} {coin['symbol']:<15} {coin['pump_score']:<6} "
                  f"{coin['price_change_24h']:>6.2f}% {coin['current_price']:<12.6f} "
                  f"{coin['quote_volume_24h']/1000000:>8.2f}M {coin.get('max_hourly_pump', 0):>7.2f}% "
                  f"{coin.get('distance_from_high', 0):>9.2f}%")
        
        print("\nLegend:")
        print("- Score: Composite pump score (higher = more significant pump)")
        print("- 24h %: 24-hour price change percentage")
        print("- Vol(USDT): 24-hour trading volume in millions USDT")
        print("- Max Hr %: Biggest single hour pump in last 24h")
        print("- From High %: Distance from 24h high (lower = still near peak)")


def main():
    """Main execution function"""
    # Initialize detector (you can add API credentials here if needed for higher rate limits)
    detector = CryptoPumpDetector()
    
    print("🔍 Crypto Pump Detector Started")
    print("Scanning Binance Futures for recently pumped coins...")
    
    try:
        # Find pumped coins with minimum score of 25
        pumped_coins = detector.find_pumped_coins(min_pump_score=25, top_n=25)
        
        # Display results
        detector.print_results(pumped_coins)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pumped_coins_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(pumped_coins, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")


if __name__ == "__main__":
    main()