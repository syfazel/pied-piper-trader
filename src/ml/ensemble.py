# src/ml/ensemble.py
from sklearn.linear_model import LogisticRegression
from src.ml.model import MarketPredictor 
from src.ml.lstm_model import LSTM_Predictor 
from src.ml.dataset import DataLabeler 
import pandas as pd
import numpy as np
import joblib
import os

class EnsemblePredictor:
    def __init__(self):
        self.predictor_A = None # LSTM
        self.predictor_B = LogisticRegression(random_state=42, solver='liblinear')
        self.aux_predictor = MarketPredictor() 
        self.is_trained = False
        self.model_file_b = "model_logistic.pkl"
        self.model_file_aux = "model_aux.pkl"

    def load_if_exists(self, sequence_length, num_features):
        """تلاش برای بارگذاری مدل‌ها به جای آموزش مجدد"""
        try:
            # بارگذاری LSTM
            self.predictor_A = LSTM_Predictor(sequence_length, num_features)
            lstm_loaded = self.predictor_A.load()
            
            # بارگذاری مدل‌های دیگر
            if lstm_loaded and os.path.exists(self.model_file_b) and os.path.exists(self.model_file_aux):
                self.predictor_B = joblib.load(self.model_file_b)
                # بارگذاری مدل کمکی (برای اینکه متد train داشته باشد، یک نمونه جدید می‌سازیم و مدل داخلی‌اش را ست می‌کنیم)
                # اما MarketPredictor ما کلاس wrapper است. ساده‌تر است که دوباره آموزش ببیند چون سریع است
                # یا اینکه آن را هم ذخیره کنیم. برای سادگی و سرعت، مدل‌های درختی سریع را می‌توانیم هر بار یا با فاصله آموزش دهیم
                # اما اینجا فرض می‌کنیم لود می‌کنیم:
                self.aux_predictor.model = joblib.load(self.model_file_aux)
                self.aux_predictor.is_trained = True
                
                self.is_trained = True
                print("⚡ Models loaded from disk. Skipping training.")
                return True
        except Exception as e:
            print(f"⚠️ Load failed: {e}")
        
        return False

    def train_all(self, X: pd.DataFrame, y: pd.Series):
        X_seq, y_target = DataLabeler.create_sequences(X, y)
        sequence_length = X_seq.shape[1]
        num_features = X_seq.shape[2]
        
        # اول سعی کن لود کنی
        if self.load_if_exists(sequence_length, num_features):
            return

        # اگر نبود، آموزش بده
        X_flat_train = X.iloc[sequence_length : len(X)] 
        
        # 1. LSTM
        self.predictor_A = LSTM_Predictor(sequence_length, num_features)
        self.predictor_A.train(X_seq, y_target)
        
        # 2. Logistic (با حفظ نام ستون‌ها برای رفع هشدار)
        self.predictor_B.fit(X_flat_train, y_target)
        joblib.dump(self.predictor_B, self.model_file_b)
        
        # 3. Auxiliary
        self.aux_predictor.train(X_flat_train, y_target)
        joblib.dump(self.aux_predictor.model, self.model_file_aux)
        
        self.is_trained = True

    def predict_combined(self, X_sample) -> tuple:
        if not self.is_trained: return 0, 0.5
            
        # LSTM Prediction
        X_sample_seq = DataLabeler.create_sequences(X_sample, pd.Series([0]*len(X_sample)))[0]
        if len(X_sample_seq) == 0: return 0, 0.5 # محافظت
        
        X_sample_seq_last = X_sample_seq[-1].reshape(1, X_sample_seq.shape[1], X_sample_seq.shape[2]) 
        prob_A = self.predictor_A.model.predict(X_sample_seq_last, verbose=0)[0][0]
        
        # Logistic Prediction (ارسال DataFrame برای حفظ نام ستون‌ها)
        X_flat_last = X_sample.iloc[[-1]] # حفظ فرمت DataFrame
        prob_B = self.predictor_B.predict_proba(X_flat_last)[0][1]
        
        final_prob = (0.70 * prob_A) + (0.30 * prob_B)
        return 1 if final_prob >= 0.5 else 0, final_prob