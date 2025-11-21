# test_phase2_backtest.py
import asyncio
import sys
import pandas as pd

# تنظیمات ویندوز
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.ingest.wallex import WallexConnector
from src.features.indicators import TechnicalFeatures
from src.strategy.scoring import SmartStrategy
from src.backtest.engine import Backtester

async def main():
    print("--- ⏳ Starting Historical Backtest ---")
    
    # 1. دریافت داده تاریخی (تعداد زیاد برای تست معنادار)
    async with WallexConnector() as exchange:
        print("1. Fetching 500 hours of history (approx 20 days)...")
        # تایم‌فریم 4 ساعته برای استراتژی‌های روندی بهتر جواب می‌دهد
        df = await exchange.fetch_ohlcv("ETHUSDT", timeframe="4h", limit=500)
        print(f"   Loaded {len(df)} candles.")

    # 2. آماده‌سازی داده‌ها
    print("2. Pre-calculating Indicators...")
    df = TechnicalFeatures.add_all(df)

    # 3. پیکربندی استراتژی و بک‌تستر
    strategy = SmartStrategy()
    # برای بک‌تست دقیق، باید ماکرو دیتا را هم تاریخی داشته باشیم.
    # اینجا برای سادگی، فرض می‌کنیم شرایط ماکرو ثابت و خنثی بوده است (یا می‌توان شبیه‌سازی کرد)
    mock_macro = {'USDT_IRT': 60000, 'GOLD_USD': 2500} 
    
    backtester = Backtester(initial_capital=1000, fee_rate=0.003) # 0.3% کارمزد

    # 4. اجرای تست
    print("3. Running Simulation...")
    # نکته: در نسخه حرفه‌ای، ماکرو دیتا باید به صورت سری زمانی پاس داده شود
    results = backtester.run(df, strategy, macro_data=mock_macro)

    # 5. نمایش نتایج
    print("\n" + "="*40)
    print("📊 BACKTEST PERFORMANCE REPORT")
    print("="*40)
    print(f"💰 Final Balance: ${results['Final Equity']} (Start: $1000)")
    print(f"📈 Return:        {results['Total Return']}")
    print(f"📉 Max Drawdown:  {results['Max Drawdown']}")
    print(f"🎲 Win Rate:      {results['Win Rate']}")
    print(f"🔄 Total Trades:  {results['Total Trades']}")
    print("-" * 40)
    
    if results['Total Trades'] > 0:
        print("\nLast 5 Trades:")
        print(results['Trade History'].tail(5)[['type', 'price', 'time', 'balance']])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nPress Enter to exit...")