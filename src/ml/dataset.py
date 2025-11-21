# src/ml/dataset.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# حافظه دید مدل
SEQUENCE_LENGTH = 24 

class DataLabeler:
    """
    آماده‌سازی داده با استراتژی Elite Features (تمرکز بر مومنتوم و روند).
    """
    @staticmethod
    def prepare(df: pd.DataFrame, target_horizon=3):
        data = df.copy()
        
        # 1. ساخت هدف (Target): پیش‌بینی سوددهی در 3 ساعت آینده
        future_close = data['close'].shift(-target_horizon)
        threshold = 0.002 
        data['target'] = (future_close > data['close'] * (1 + threshold)).astype(int)
        
        # 2. انتخاب ویژگی‌های برنده (Elite Features)
        # این لیست بر اساس آنالیز اهمیت ویژگی‌ها (SHAP) و پایداری انتخاب شده است
        feature_cols = [
            'sma_50',            # روند کلی (قدرتمندترین درایور)
            'pct_change_3h',     # شتاب میان‌مدت
            'pct_change_24h',    # روند روزانه (جدید)
            'vol_ratio',         # فشار پول هوشمند
            'macd_hist'          # تغییر فاز بازار
        ]
        
        # بررسی موجود بودن ستون‌ها
        available_cols = [c for c in feature_cols if c in data.columns]
        
        if len(available_cols) < len(feature_cols):
            missing = set(feature_cols) - set(available_cols)
            print(f"⚠️ Warning: Missing features: {missing}")

        # حذف ردیف‌های خالی
        data.dropna(subset=available_cols, inplace=True)
        
        # 3. نرمال‌سازی داده‌ها (Scaling)
        scaler = MinMaxScaler(feature_range=(0, 1))
        
        if not data.empty:
            scaled_data = scaler.fit_transform(data[available_cols])
            
            # تبدیل دوباره به DataFrame
            df_scaled = pd.DataFrame(scaled_data, columns=available_cols, index=data.index)
            
            targets = data['target'].loc[df_scaled.index]
            valid_indices = ~np.isnan(targets)
            
            return df_scaled[valid_indices], targets[valid_indices], scaler
        else:
            return pd.DataFrame(), pd.Series(), scaler

    @staticmethod
    def create_sequences(X, y):
        """
        تبدیل داده‌های 2D به توالی‌های 3D برای LSTM.
        """
        X_values = X.values
        y_values = y.values
        
        X_sequences, y_targets = [], []
        
        if len(X_values) > SEQUENCE_LENGTH:
            for i in range(SEQUENCE_LENGTH, len(X_values)):
                X_sequences.append(X_values[i - SEQUENCE_LENGTH : i])
                y_targets.append(y_values[i])
        
        return np.array(X_sequences), np.array(y_targets)