# test_phase4_full.py
import asyncio
import sys
import traceback

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.ingest.wallex import WallexConnector
from src.features.indicators import TechnicalFeatures
from src.strategy.scoring import SmartStrategy
from src.ml.model import MarketPredictor
from src.ml.dataset import DataLabeler
from src.nlp.sentiment import NewsAnalyzer
from src.reporting.generator import ReportGenerator

async def main():
    print("--- 🚀 STARTING FULL SYSTEM TEST (Phase 4) ---")
    
    # 1. دریافت داده
    print("1. Ingesting Data...")
    async with WallexConnector() as exchange:
        df = await exchange.fetch_ohlcv("ETHUSDT", timeframe="1h", limit=500)
    
    # 2. پردازش
    print("2. Processing Features...")
    df = TechnicalFeatures.add_all(df)
    
    # 3. هوش مصنوعی (آموزش سریع و پیش‌بینی)
    print("3. Running AI Model...")
    labeler = DataLabeler()
    X, y = labeler.prepare(df)
    predictor = MarketPredictor()
    predictor.train(X, y)
    
    last_features = X.tail(1)
    ai_prediction = predictor.predict(last_features) # (signal, probability)
    
    # 4. تحلیل احساسات (Simulated)
    print("4. Analyzing Sentiment...")
    nlp = NewsAnalyzer()
    # اینجا چند تیتر تستی می‌دهیم
    fake_news = ["Bitcoin ETF approved", "Market shows strong recovery", "Inflation is rising"]
    sentiment_res = nlp.analyze_headlines(fake_news)
    
    # 5. استراتژی نهایی
    print("5. Executing Strategy Engine...")
    strategy = SmartStrategy()
    # ماکرو دیتای فرضی
    macro_data = {'USDT_IRT': 69500, 'GOLD_USD': 2750}
    
    # استراتژی از امتیاز سنتیمنت هم استفاده می‌کند
    strategy_res = strategy.analyze(
        df, 
        macro_data=macro_data, 
        sentiment_score=sentiment_res['sentiment_score']
    )
    
    # 6. تولید گزارش
    print("\nGenerating Final Report...")
    final_report = ReportGenerator.create_report(
        symbol="ETH/USDT",
        strategy_result=strategy_res,
        ai_result=ai_prediction,
        sentiment_result=sentiment_res
    )
    
    print(final_report)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
    
    print("\nPress Enter to exit...")