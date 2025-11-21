# src/ingest/wallex.py
import pandas as pd
import time
import aiohttp
import requests
from .base import BaseConnector
from src.core.types import OHLCV_COLUMNS
from src.core.utils import LOGGER

class WallexConnector(BaseConnector):
    def __init__(self):
        super().__init__("Wallex")
        self.base_url = "https://api.wallex.ir/v1/udf/history"
        self.market_url = "https://api.wallex.ir/v1/markets"
        # تنظیمات اتصال (بدون پروکسی برای سرور ایران)
        self.proxies = {"http": None, "https": None}

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        # --- FIX: تغییر پیش‌فرض به تومان (TMN) ---
        clean_symbol = symbol.upper().replace('-', '').replace('/', '')
        
        # اگر کاربر نگفت چی، پیش‌فرض تومان بگذار
        if not clean_symbol.endswith('USDT') and not clean_symbol.endswith('TMN'):
            clean_symbol += 'TMN'

        to_ts = int(time.time())
        tf_map = {'15m': 15, '1h': 60, '4h': 240}
        minutes = tf_map.get(timeframe, 60)
        from_ts = to_ts - (minutes * 60 * (limit + 50)) # کمی بیشتر بگیر

        params = {
            'symbol': clean_symbol,
            'resolution': str(minutes),
            'from': from_ts,
            'to': to_ts
        }
        
        LOGGER.info(f"INGEST: Requesting {clean_symbol} (Toman Base)...") 
        
        if not self.session:
            raise RuntimeError("Session not started.")

        try:
            async with self.session.get(self.base_url, params=params, timeout=15) as response:
                if response.status != 200: raise Exception(f"HTTP {response.status}")
                data = await response.json()
                if data.get('s') != 'ok': raise Exception("API Error")

                df = pd.DataFrame({
                    'timestamp': pd.to_datetime(data['t'], unit='s'),
                    'open': data['o'], 'high': data['h'], 'low': data['l'], 
                    'close': data['c'], 'volume': data['v']
                })
                
                # تبدیل به float
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].astype(float)
                
                return df[OHLCV_COLUMNS].tail(limit)
        except Exception as e:
            LOGGER.critical(f"WALLEX FAIL: {e}")
            raise

    def get_macro_prices(self):
        """دریافت قیمت لحظه‌ای دلار و طلا به تومان"""
        print("📊 Fetching Macro Data (Toman)...")
        macro = {"USDT_IRT": 0, "GOLD_IRT": 0} # نام‌ها را به IRT تغییر دادیم

        try:
            res = requests.get(self.market_url, timeout=10, proxies=self.proxies)
            data = res.json()
            
            if data['success']:
                symbols = data['result']['symbols']
                
                # 1. قیمت دلار (USDTTMN)
                if 'USDTTMN' in symbols:
                    macro['USDT_IRT'] = float(symbols['USDTTMN']['stats']['lastPrice'])
                
                # 2. قیمت طلا (PAXGTMN)
                # اگر جفت ارز مستقیم طلا/تومان بود:
                if 'PAXGTMN' in symbols:
                    macro['GOLD_IRT'] = float(symbols['PAXGTMN']['stats']['lastPrice'])
                # اگر نبود، محاسبه کن: PAXGUSDT * USDTTMN
                elif 'PAXGUSDT' in symbols:
                    paxg_usd = float(symbols['PAXGUSDT']['stats']['lastPrice'])
                    macro['GOLD_IRT'] = paxg_usd * macro['USDT_IRT']
            
            return macro
        except Exception as e:
            LOGGER.error(f"MACRO ERROR: {e}")
            return macro