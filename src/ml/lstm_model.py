# src/ml/lstm_model.py
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from sklearn.metrics import precision_score
from sklearn.model_selection import train_test_split
import numpy as np
import os

class LSTM_Predictor:
    def __init__(self, sequence_length=None, num_features=None, model_path="lstm_model.keras"):
        self.model_path = model_path
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.model = None
        self.is_trained = False

    def build_model(self):
        """ساخت معماری استاندارد بدون هشدار"""
        model = Sequential([
            Input(shape=(self.sequence_length, self.num_features)), # FIX: لایه ورودی صریح
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(1, activation='sigmoid') 
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def train(self, X_seq, y_target):
        # اگر مدل وجود نداشت، بساز
        if self.model is None:
            self.model = self.build_model()

        X_train, X_test, y_train, y_test = train_test_split(X_seq, y_target, test_size=0.2, shuffle=False)
        
        print(f"🤖 Training LSTM on {len(X_train)} sequences...")
        self.model.fit(X_train, y_train, epochs=15, batch_size=32, verbose=0)
        
        # ذخیره مدل آموزش دیده
        self.model.save(self.model_path)
        self.is_trained = True
        
        preds = (self.model.predict(X_test, verbose=0) > 0.5).astype(int)
        return precision_score(y_test, preds, zero_division=0)

    def load(self):
        """بارگذاری مدل ذخیره شده برای جلوگیری از آموزش مجدد"""
        if os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                self.is_trained = True
                return True
            except:
                return False
        return False
        
    def predict(self, X_sample):
        if not self.is_trained: return 0, 0.5
        if X_sample.ndim == 2:
            X_sample = np.expand_dims(X_sample, axis=0)
        prob = self.model.predict(X_sample, verbose=0)[0][0]
        return (prob > 0.5).astype(int), prob