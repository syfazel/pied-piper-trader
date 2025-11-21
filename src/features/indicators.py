# src/features/indicators.py
import pandas as pd
import pandas_ta as ta 

class TechnicalFeatures:
    """
    موتور محاسبات برداری (شامل تمامی ویژگی‌های Elite).
    """
    @staticmethod
    def add_all(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # 1. Trend Indicators
        df['sma_20'] = ta.sma(df['close'], length=20)
        df['sma_50'] = ta.sma(df['close'], length=50)
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df['macd_line'] = macd.iloc[:, 0]
            df['macd_hist'] = macd.iloc[:, 1]
            df['macd_signal'] = macd.iloc[:, 2]
        
        # 2. Volatility
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        bb = ta.bbands(df['close'], length=20, std=2)
        if bb is not None:
            cols = bb.columns.tolist()
            upper = [c for c in cols if c.startswith("BBU")][0]
            lower = [c for c in cols if c.startswith("BBL")][0]
            df['bb_upper'] = bb[upper]
            df['bb_lower'] = bb[lower]
        
        # 3. ADX & OBV
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx is not None:
            df['adx'] = adx.iloc[:, 0]

        df['obv'] = ta.obv(df['close'], df['volume'])
        
        vol_ma = df['volume'].rolling(window=20).mean()
        df['vol_ratio'] = df['volume'] / vol_ma
        
        # 4. Ratios
        df['price_sma_ratio'] = df['close'] / df['sma_50']
        df['volatility_ratio'] = df['close'] / df['close'].shift(1)
        
        # 5. Lag Features
        df['pct_change_1h'] = df['close'].pct_change(1)
        df['pct_change_3h'] = df['close'].pct_change(3)
        
        # --- FIX: اضافه کردن ویژگی گم شده ---
        df['pct_change_24h'] = df['close'].pct_change(24)
        
        df['rsi_diff'] = df['rsi'].diff()

        df.dropna(inplace=True)
        return df