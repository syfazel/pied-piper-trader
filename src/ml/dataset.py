# src/ml/dataset.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler # استفاده از اسکیلر مقاوم‌تر

SEQUENCE_LENGTH = 24

class DataLabeler:
    @staticmethod
    def get_volatility(close, span0=100):
        """محاسبه نوسان روزانه برای تعیین حد سود/ضرر پویا"""
        df0 = close.pct_change()
        return df0.ewm(span=span0).std()

    @staticmethod
    def apply_triple_barrier(close, volatility, t_events, pt=1, sl=1, min_ret=0.002):
        """
        Triple Barrier Method (Marcos Lopez de Prado)
        تعیین هدف بر اساس نوسان بازار (نه درصد ثابت)
        """
        # 1. حد بالا (سود) و پایین (ضرر) بر اساس نوسان لحظه‌ای
        upper = volatility * pt # Profit Take
        lower = -volatility * sl # Stop Loss
        
        labels = pd.Series(index=t_events)
        
        for t in t_events:
            path = close[t:] # مسیر قیمت از این لحظه به بعد
            # افق زمانی: حداکثر 24 ساعت
            path = path.head(24) 
            
            # اولین جایی که به حد سود یا ضرر می‌رسد
            break_up = path[path > close[t] * (1 + upper[t])].index.min()
            break_down = path[path < close[t] * (1 + lower[t])].index.min()
            
            if pd.isna(break_up) and pd.isna(break_down):
                labels[t] = 0 # خنثی (به زمان خوردیم)
            elif pd.isna(break_down):
                labels[t] = 1 # سود (اول به بالا خورد)
            elif pd.isna(break_up):
                labels[t] = 0 # ضرر (اول به پایین خورد - ما کلاس 0 می‌گذاریم که نخریم)
            else:
                # هر کدام زودتر اتفاق افتاد
                labels[t] = 1 if break_up < break_down else 0
                
        return labels.dropna()

    @staticmethod
    def prepare(df: pd.DataFrame):
        data = df.copy()
        
        # محاسبه نوسان پویا
        data['volatility'] = DataLabeler.get_volatility(data['close'])
        
        # برچسب‌گذاری پیشرفته (Triple Barrier)
        # هدف: سود 2 برابر نوسان، ضرر 1 برابر نوسان (Risk/Reward 1:2)
        labels = DataLabeler.apply_triple_barrier(
            data['close'], data['volatility'], data.index, pt=2, sl=1
        )
        
        data['target'] = labels
        
        # ویژگی‌های ورودی (شامل ویژگی‌های جدید فراکتالی در آینده)
        feature_cols = [
            'close', 'rsi', 'macd_hist', 'sma_50', 'obv', 
            'price_sma_ratio', 'volatility_ratio', 'pct_change_3h',
            'volatility' # نوسان هم به عنوان ورودی مهم است
        ]
        
        # همگام‌سازی
        data = data.loc[labels.index]
        available_cols = [c for c in feature_cols if c in data.columns]
        data.dropna(subset=available_cols, inplace=True)
        
        # نرمال‌سازی مقاوم (Robust Scaler بهتر از MinMax در مالی است)
        scaler = RobustScaler()
        scaled_data = scaler.fit_transform(data[available_cols])
        
        df_scaled = pd.DataFrame(scaled_data, columns=available_cols, index=data.index)
        return df_scaled, data['target'], scaler

    @staticmethod
    def create_sequences(X, y):
        # (کد قبلی برای توالی‌سازی)
        X_values = X.values
        y_values = y.values
        X_seq, y_target = [], []
        for i in range(SEQUENCE_LENGTH, len(X_values)):
            X_seq.append(X_values[i - SEQUENCE_LENGTH : i])
            y_target.append(y_values[i])
        return np.array(X_seq), np.array(y_target)