# src/core/types.py
import pandas as pd
from enum import Enum

class TimeFrame(Enum):
    M1 = '1m'
    M5 = '5m'
    M15 = '15m'
    H1 = '1h'
    H4 = '4h'
    D1 = '1d'

# ستون‌های استاندارد اجباری برای تمام دیتافریم‌ها
OHLCV_COLUMNS = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    تضمین می‌کند که دیتافریم ورودی استاندارد است.
    """
    # بررسی وجود ستون‌های ضروری
    if not all(col in df.columns for col in OHLCV_COLUMNS):
        raise ValueError(f"DataFrame must contain columns: {OHLCV_COLUMNS}")
    
    # تضمین فرمت زمانی (UTC)
    if df['timestamp'].dtype != 'datetime64[ns, UTC]':
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None) # حذف تایم‌زون قبلی اگر دارد
    
    return df