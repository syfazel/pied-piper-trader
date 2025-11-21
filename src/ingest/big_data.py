# src/ingest/big_data.py
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

class BigDataManager:
    def __init__(self, csv_path="data/history_50k.csv"):
        self.csv_path = csv_path
        os.makedirs("data", exist_ok=True)

    def get_combined_data(self, live_df: pd.DataFrame, target_size=50000):
        """
        ترکیب هوشمند داده‌ها با تضمین سلامت داده.
        """
        # 1. تمیزکاری دیتای زنده
        live_df = self._clean_dataframe(live_df)

        # 2. بارگذاری تاریخچه
        historical_df = self._load_history()
        historical_df = self._clean_dataframe(historical_df)

        # 3. ترکیب (Concat)
        if not historical_df.empty and not live_df.empty:
            combined_df = pd.concat([historical_df, live_df])
        elif not historical_df.empty:
            combined_df = historical_df
        else:
            combined_df = live_df

        # 4. حذف تکراری‌ها و مرتب‌سازی
        combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
        combined_df.sort_index(inplace=True)
        
        # 5. --- FIX: استفاده از ffill به جای interpolate ---
        # استفاده از interpolate(method='time') باعث ارور NotImplementedError می‌شد.
        # ffill (Forward Fill) داده‌های گم شده را با آخرین قیمت معتبر پر می‌کند که امن‌تر است.
        combined_df = combined_df.ffill()
        
        # حذف هرگونه NaN باقی‌مانده (مثلاً در ابتدای دیتا)
        combined_df.dropna(inplace=True)

        # محدود کردن به سایز هدف (مثلا 50 هزار تا) برای جلوگیری از سنگین شدن
        if len(combined_df) > target_size:
            combined_df = combined_df.tail(target_size)

        print(f"📊 Data Merge Stats: Total={len(combined_df)} candles")
        return combined_df

    def _clean_dataframe(self, df):
        """
        تابع کمکی برای استانداردسازی فرمت زمان و حذف NaN
        """
        if df is None or df.empty:
            return pd.DataFrame()

        # اطمینان از اینکه ایندکس زمان است
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                # تلاش برای تبدیل ایندکس به datetime
                df.index = pd.to_datetime(df.index)
            except:
                return pd.DataFrame() # اگر تبدیل نشد، دیتای خراب برگردان
        
        # حذف تایم‌زون
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # اطمینان از اینکه ستون‌ها عددی هستند (جلوگیری از ارور در محاسبات)
        cols = ['open', 'high', 'low', 'close', 'volume']
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # حذف ردیف‌هایی که قیمت یا حجم ندارند (NaN شدند)
        df.dropna(subset=['close', 'volume'], inplace=True)
        
        return df

    def _load_history(self):
        if os.path.exists(self.csv_path):
            try:
                # خواندن CSV با پارس کردن صحیح ایندکس
                df = pd.read_csv(self.csv_path, index_col=0, parse_dates=True)
                return df
            except Exception as e:
                print(f"⚠️ Corrupt CSV: {e}. Starting fresh.")
                # اگر فایل خراب بود حذفش کن
                try:
                    os.remove(self.csv_path)
                except: pass
                return pd.DataFrame()
        return pd.DataFrame()