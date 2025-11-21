# src/ml/ensemble.py
from sklearn.linear_model import LogisticRegression
from src.ml.model import MarketPredictor
from src.ml.lstm_model import LSTM_Predictor
from src.ml.dataset import DataLabeler
import pandas as pd
import numpy as np

class EnsemblePredictor:
    def __init__(self):
        self.predictor_A = None 
        self.predictor_B = LogisticRegression(random_state=42, solver='liblinear')
        self.aux_predictor = MarketPredictor() 
        self.is_trained = False

    def train_all(self, X: pd.DataFrame, y: pd.Series):
        """آموزش تمام مدل‌ها"""
        
        # 1. آماده‌سازی برای LSTM
        X_seq, y_target = DataLabeler.create_sequences(X, y)
        
        # 2. برش برای مدل‌های 2D
        sequence_length = X_seq.shape[1]
        X_flat_train = X.iloc[sequence_length : len(X)] 
        
        # --- آموزش مدل A (LSTM) ---
        num_features = X_seq.shape[2]
        self.predictor_A = LSTM_Predictor(sequence_length, num_features)
        print("🤖 [Ensemble] Training Model A (LSTM - Sequence)...")
        self.predictor_A.train(X_seq, y_target)
        
        # --- آموزش مدل B (Logistic) ---
        print("🤖 [Ensemble] Training Model B (Logistic Regression - Simple)...")
        self.predictor_B.fit(X_flat_train, y_target)
        
        # --- آموزش مدل کمکی (Auxiliary - SHAP) ---
        print("🤖 [Ensemble] Training Auxiliary Model (for SHAP)...")
        # الان MarketPredictor اصلاح شده و با آرایه نامپای y_target هم کار می‌کند
        self.aux_predictor.train(X_flat_train, y_target) 
        
        self.is_trained = True

    def predict_combined(self, X_sample: pd.DataFrame) -> tuple:
        """
        پیش‌بینی نهایی.
        X_sample: دقیقا 10 ردیف آخر دیتافریم (DataFrame)
        """
        if not self.is_trained:
            return 0, 0.5
            
        # --- FIX: تبدیل دستی به فرمت 3D برای پیش‌بینی ---
        # به جای create_sequences که نیاز به دیتای بیشتر دارد،
        # مستقیماً داده را به شکل (1, 10, Features) در می‌آوریم.
        
        X_values = X_sample.values # تبدیل به NumPy
        # Reshape: [Batch Size=1, Timesteps=10, Features=N]
        X_sample_seq_last = X_values.reshape(1, X_values.shape[0], X_values.shape[1])
        
        # 1. پیش‌بینی LSTM
        prob_A = self.predictor_A.model.predict(X_sample_seq_last, verbose=0)[0][0]
        
        # 2. پیش‌بینی Logistic (فقط آخرین کندل)
        X_flat_last = X_sample.iloc[-1].values.reshape(1, -1)
        prob_B = self.predictor_B.predict_proba(X_flat_last)[0][1]
        
        # 3. ترکیب (70% LSTM, 30% Logistic)
        final_prob = (0.70 * prob_A) + (0.30 * prob_B)
        final_prediction = 1 if final_prob >= 0.5 else 0
        
        return final_prediction, final_prob