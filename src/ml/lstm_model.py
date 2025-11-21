# src/ml/lstm_model.py (NEW FILE)
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import precision_score
from sklearn.model_selection import train_test_split
import numpy as np

class LSTM_Predictor:
    """
    مدل LSTM برای پیش‌بینی توالی داده‌های مالی.
    """
    def __init__(self, sequence_length, num_features):
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.model = self._build_model()
        self.is_trained = False

    def _build_model(self):
        """ساخت معماری شبکه عصبی LSTM."""
        model = Sequential([
            # لایه LSTM: 50 واحد، ورودی 3D
            LSTM(50, input_shape=(self.sequence_length, self.num_features), return_sequences=False),
            Dropout(0.2), # جلوگیری از Overfitting
            # لایه خروجی: 1 واحد (Binary Classification: Buy/Sell)
            Dense(1, activation='sigmoid') 
        ])
        
        # کامپایل مدل
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def train(self, X_seq: np.ndarray, y_target: np.ndarray):
        """آموزش مدل روی داده‌های توالی"""
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_seq, y_target, test_size=0.2, shuffle=False
        )
        
        print(f"🤖 Training LSTM on {len(X_train)} sequences...")
        
        # آموزش
        self.model.fit(
            X_train, y_train,
            epochs=15, # تعداد دور آموزش
            batch_size=32,
            verbose=0 # نمایش ندادن خروجی در حین آموزش
        )
        
        # ارزیابی
        preds = (self.model.predict(X_test) > 0.5).astype(int)
        precision = precision_score(y_test, preds, zero_division=0)
        
        self.is_trained = True
        return precision
        
    def predict(self, X_sample: np.ndarray) -> tuple:
        """پیش‌بینی برای یک نمونه 3D"""
        if not self.is_trained:
            return 0, 0.5
            
        # نمونه ورودی باید حتماً [1, timesteps, features] باشد
        if X_sample.ndim == 2:
            X_sample = np.expand_dims(X_sample, axis=0)

        prob = self.model.predict(X_sample)[0][0]
        prediction = (prob > 0.5).astype(int)
        
        return prediction, prob