import pandas as pd
import numpy as np

class DataGuard:
    """
    لایه محافظتی برای جلوگیری از ورود داده‌های زباله (GIGO) به مدل هوش مصنوعی.
    استاندارد 2025: Data-Centric AI
    """
    
    @staticmethod
    def check_data_health(df: pd.DataFrame) -> dict:
        """
        بررسی سلامت دیتافریم قبل از پردازش.
        خروجی: { 'is_healthy': bool, 'reason': str }
        """
        if df is None or df.empty:
            return {'is_healthy': False, 'reason': 'CRITICAL: Empty Dataframe'}

        # 1. چک کردن قیمت صفر (Market Offline)
        last_price = df.iloc[-1]['close']
        if last_price <= 0:
            return {'is_healthy': False, 'reason': f'CRITICAL: Price is Zero ({last_price})'}

        # 2. چک کردن داده‌های گم شده (NaN)
        if df.isnull().values.any():
            # اگر تعداد NaN کم باشد (زیر 5%)، قابل تعمیر است، اما اینجا سخت‌گیرانه عمل می‌کنیم
            return {'is_healthy': False, 'reason': 'WARNING: NaN values detected'}

        # 3. چک کردن جمود بازار (Zero Variance)
        # اگر قیمت در 5 کندل آخر تکان نخورده باشد، پیش‌بینی بی‌معنی است
        recent_volatility = df['close'].tail(5).std()
        if recent_volatility == 0:
             return {'is_healthy': False, 'reason': 'WARNING: Market Frozen (Zero Variance)'}

        return {'is_healthy': True, 'reason': 'Stable'}