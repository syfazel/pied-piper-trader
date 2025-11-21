# test_phase1.py
import asyncio
import traceback
# اگر روی ویندوز هستید، این خط برای جلوگیری از برخی ارورهای خاص async لازم است
import sys

# تنظیم سیاست رویداد برای ویندوز (اختیاری ولی توصیه شده)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.ingest.wallex import WallexConnector

async def main():
    print("--- 🚀 Starting Next-Gen Ingestor Test ---")
    print("1. Initializing Connector...")
    
    # استفاده از Context Manager برای مدیریت اتصال
    async with WallexConnector() as exchange:
        try:
            print("2. Requesting Data from Wallex...")
            df = await exchange.fetch_ohlcv("ETHUSDT", timeframe="1h", limit=10)
            
            print("\n✅ Data Received Successfully:")
            print("=" * 50)
            print(df.head())
            print("=" * 50)
            print(f"\n📊 Columns: {df.columns.tolist()}")
            print(f"🔢 Rows: {len(df)}")
            
        except Exception as e:
            print(f"\n❌ ERROR during fetch: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        traceback.print_exc()
    
    # 👇👇👇 این خط جادویی باعث می‌شود پنجره باز بماند 👇👇👇
    print("\n" + "-"*30)
    input("Press Enter key to exit...")