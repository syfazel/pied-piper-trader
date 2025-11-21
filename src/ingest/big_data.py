# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

class BigDataManager:
    """
    مدیریت داده‌های حجیم برای آموزش عمیق LSTM.
    ترکیب داده‌های CSV (تاریخی) با API (زنده).
    """
    def __init__(self, csv_path="data/history_50k.csv"):
        self.csv_path = csv_path
        # اگر پوشه دیتا نیست بساز
        os.makedirs("data", exist_ok=True)

    def get_combined_data(self, live_df: pd.DataFrame, target_size=50000):
        """
        داده‌های زنده را می‌گیرد و با داده‌های تاریخی ترکیب می‌کند.
        """
        # 1. استانداردسازی ایندکس دیتای زنده
        live_df.index = pd.to_datetime(live_df.index)
        # حذف تایم‌زون برای جلوگیری از تداخل
        if live_df.index.tz is not None:
            live_df.index = live_df.index.tz_localize(None)

        # 2. بارگذاری یا تولید تاریخچه
        historical_df = self._load_or_generate_history(target_size, live_df)
        
        # 3. استانداردسازی ایندکس دیتای تاریخی
        historical_df.index = pd.to_datetime(historical_df.index)
        if historical_df.index.tz is not None:
            historical_df.index = historical_df.index.tz_localize(None)

        # 4. ترکیب داده‌ها
        combined_df = pd.concat([historical_df, live_df])
        
        # 5. حذف تکراری‌ها و مرتب‌سازی
        # (اولویت با داده‌های جدیدتر است)
        combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
        combined_df.sort_index(inplace=True)
        
        print(f"📊 Data Merge Complete: {len(combined_df)} candles.")
        return combined_df

    def _load_or_generate_history(self, size, reference_df):
        if os.path.exists(self.csv_path):
            try:
                print("📂 Loading historical data from CSV...")
                
                # --- FIX: خواندن صحیح ایندکس زمانی ---
                # پارامتر index_col=0 اولین ستون را به عنوان ایندکس می‌گیرد
                # پارامتر parse_dates=True آن را به فرمت زمان تبدیل می‌کند
                df = pd.read_csv(self.csv_path, index_col=0, parse_dates=True)
                
                # اطمینان از نام ایندکس
                df.index.name = 'timestamp'
                
                # حذف ردیف‌های خراب (فقط اگر دیتای حیاتی ندارند)
                df.dropna(subset=['close', 'volume'], inplace=True)
                
                return df
            except Exception as e:
                print(f"⚠️ Error loading CSV (Regenerating...): {e}")
                # اگر فایل خراب بود، حذفش کن تا دوباره ساخته شود
                os.remove(self.csv_path)
        
        print("⚡ Generating SYNTHETIC history...")
        return self._generate_synthetic_history(size, reference_df)

    def _generate_synthetic_history(self, count, ref_df):
        # گرفتن آخرین زمان از دیتای زنده برای اتصال نرم
        if not ref_df.empty:
            raw_time = ref_df.index[0]
            last_real_price = ref_df.iloc[0]['close']
        else:
            # حالت اضطراری اگر دیتای زنده هم نیامده باشد
            raw_time = datetime.now()
            last_real_price = 100000000

        last_real_time = pd.to_datetime(raw_time)
        if last_real_time.tz is not None:
             last_real_time = last_real_time.tz_localize(None)

        # تولید زمان‌های گذشته
        timestamps = [last_real_time - timedelta(hours=i) for i in range(1, count + 1)]
        timestamps.reverse()
        
        # تولید قیمت (Random Walk)
        prices = []
        price = last_real_price
        for _ in range(count):
            change = np.random.normal(0, 0.005) 
            price = price * (1 + change)
            prices.append(price)
            
        df = pd.DataFrame(index=timestamps)
        df.index.name = 'timestamp'
        df['close'] = prices
        
        # ساخت بقیه ستون‌ها
        df['open'] = df['close'] * (1 + np.random.normal(0, 0.001, count))
        df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.005, count))
        df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.005, count))
        df['volume'] = np.random.randint(100, 10000, count).astype(float)
        
        # ذخیره در CSV
        df.to_csv(self.csv_path)
        print(f"💾 History saved to {self.csv_path}")
        
        return df