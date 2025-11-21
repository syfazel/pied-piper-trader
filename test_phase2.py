# test_phase2.py
import asyncio
import sys
import traceback

# تنظیمات ویندوز
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.ingest.wallex import WallexConnector
from src.features.indicators import TechnicalFeatures
from src.strategy.scoring import SmartStrategy

async def main():
    print("--- 🧠 Testing Phase 2: Analytics & Strategy Engine ---")
    
    async with WallexConnector() as exchange:
        print("1. Fetching Live Data...")
        # دریافت 100 کندل آخر برای محاسبه دقیق اندیکاتورها
        df = await exchange.fetch_ohlcv("ETHUSDT", timeframe="1h", limit=100)
        
        print("2. Calculating Technical Features...")
        df_analyzed = TechnicalFeatures.add_all(df)
        # نمایش آخرین مقادیر محاسبه شده
        print(df_analyzed[['close', 'rsi', 'sma_50', 'bb_upper']].tail(3))
        
        print("\n3. Running Strategy Engine...")
        strategy = SmartStrategy()
        
        # دیتای ماکروی فرضی برای تست (در فازهای بعد زنده می‌شود)
        mock_macro = {'USDT_IRT': 69000, 'GOLD_USD': 2700}
        
        result = strategy.analyze(df_analyzed, macro_data=mock_macro)
        
        print("\n" + "="*40)
        print(f"📢 FINAL SIGNAL: {result['action']}")
        print(f"📊 SCORE: {result['score']}/100")
        print(f"🔍 REASONS: {result['reasons']}")
        print(f"📈 DETAIL: Tech:{result['components']['technical']} | Macro:{result['components']['macro']}")
        print("="*40)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        traceback.print_exc()
    
    print("\n" + "-"*30)
    input("Press Enter key to exit...")