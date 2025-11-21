# src/ml/model.py
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import precision_score
import numpy as np
import pandas as pd
import shap 

class MarketPredictor:
    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=200,       
            learning_rate=0.01,     
            max_depth=4,            
            min_samples_split=20,   
            subsample=0.9,          
            random_state=42
        )
        self.is_trained = False

    def train(self, X, y):
        """آموزش مدل با گزارش‌دهی بدون فیلتر (Raw Precision)"""
        print(f"🤖 Training AI model on {len(X)} samples...")
        
        split = int(len(X) * 0.8)
        
        if isinstance(X, pd.DataFrame):
            X_train, X_test = X.iloc[:split], X.iloc[split:]
        else:
            X_train, X_test = X[:split], X[split:]
            
        if isinstance(y, pd.Series):
            y_train, y_test = y.iloc[:split], y.iloc[split:]
        else:
            y_train, y_test = y[:split], y[split:]
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # --- FIX: گزارش دقت واقعی (بدون فیلتر 55%) ---
        if len(X_test) > 0:
            # پیش‌بینی استاندارد (بالای 50% = خرید)
            preds = self.model.predict(X_test)
            
            # محاسبه دقت روی تمام سیگنال‌ها
            precision = precision_score(y_test, preds, zero_division=0)
            count = np.sum(preds) # تعداد کل سیگنال‌های خرید
            
            print(f"✅ Model Trained. RAW Precision: {precision:.2%} (on {count} trades)")
            return precision
            
        return 0.0

    def predict(self, current_features):
        if not self.is_trained: return 0, 0.5
        try:
            prediction = self.model.predict(current_features)[0]
            probability = self.model.predict_proba(current_features)[0][1]
            return prediction, probability
        except Exception as e:
            print(f"Prediction Error: {e}")
            return 0, 0.5

    def get_feature_importance(self, X_sample):
        if not self.is_trained or (hasattr(X_sample, 'empty') and X_sample.empty):
            return []
        try:
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(X_sample)[0] 
            
            if hasattr(X_sample, 'columns'):
                feature_names = X_sample.columns.tolist()
            else:
                feature_names = [f"F{i}" for i in range(X_sample.shape[1])]

            importance = {name: float(np.abs(val)) for name, val in zip(feature_names, shap_values)}
            return sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        except:
            return []