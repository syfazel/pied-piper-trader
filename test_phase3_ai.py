# test_phase3_ai.py
import asyncio
import sys
import pandas as pd

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.ingest.wallex import WallexConnector
from src.features.indicators import TechnicalFeatures
from src.ml.dataset import DataLabeler
from src.ml.model import MarketPredictor

async def main():
    print("--- 🤖 Phase 3: AI Model Training & Prediction ---")
    
    async with WallexConnector() as exchange:
        # 1. دریافت داده زیاد برای آموزش (مثلا 2000 کندل)
        print("1. Fetching training data (2000 candles)...")
        df = await exchange.fetch_ohlcv("ETHUSDT", timeframe="1h", limit=1000)

    # 2. محاسبه اندیکاتورها
    df = TechnicalFeatures.add_all(df)
    
    # 3. آماده‌سازی دیتاست (X, y)
    print("2. Preparing Dataset...")
    labeler = DataLabeler()
    X, y = labeler.prepare(df)
    
    # 4. آموزش مدل
    predictor = MarketPredictor()
    precision = predictor.train(X, y)
    
    if precision < 0.5:
        print("⚠️ Warning: Model precision is low. Needs more data or features.")
    
    # 5. پیش‌بینی زنده (روی آخرین کندل موجود)
    print("\n3. Live Prediction Test...")
    last_features = X.tail(1) # آخرین وضعیت بازار
    signal, confidence = predictor.predict(last_features)
    
    print("="*40)
    print(f"🔮 AI PREDICTION for next hour:")
    if signal == 1:
        print(f"🚀 ACTION: BUY (Confidence: {confidence:.1%})")
    else:
        print(f"🛑 ACTION: WAIT/SELL (Confidence: {1-confidence:.1%})")
    print("="*40)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
    print("\nPress Enter to exit...")