# src/ml/tuner.py
import sys
import os

# --- FIX: افزودن ریشه پروژه به مسیر پایتون ---
# این خط باعث می‌شود پایتون پوشه اصلی پروژه را پیدا کند
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.ensemble import GradientBoostingClassifier

# اکنون ایمپورت‌ها بدون خطا کار می‌کنند
from src.ingest.big_data import BigDataManager
from src.features.indicators import TechnicalFeatures
from src.ml.dataset import DataLabeler

def run_tuning():
    print("🧪 Starting Hyperparameter Tuning (Optimization)...")
    
    # 1. بارگذاری داده‌ها
    mgr = BigDataManager()
    # اگر فایل دیتا نبود، ارور نده، بلکه تلاش کن بسازی یا لود کنی
    if not os.path.exists("data/history_50k.csv"):
        print("❌ Data file not found. Please run the main app first to generate data.")
        return

    # بارگذاری کل دیتا برای تیونینگ
    print("📂 Loading 50k dataset...")
    df = pd.read_csv("data/history_50k.csv", index_col=0, parse_dates=True)
    print(f"   Data loaded: {len(df)} rows")
    
    # 2. پردازش
    print("⚙️ Calculating Indicators...")
    df = TechnicalFeatures.add_all(df)
    
    print("🏷️ Labeling & Scaling...")
    labeler = DataLabeler()
    # توجه: اینجا فقط به X و y نیاز داریم، Scaler را نادیده می‌گیریم
    X, y, _ = labeler.prepare(df)
    
    # 3. تعریف فضای جستجو (Grid)
    param_dist = {
        'n_estimators': [200, 400, 600, 800],
        'learning_rate': [0.01, 0.03, 0.05, 0.1],
        'max_depth': [3, 4, 5, 6],
        'min_samples_split': [10, 20, 50],
        'subsample': [0.8, 0.9, 1.0]
    }
    
    # 4. مدل پایه
    model = GradientBoostingClassifier(random_state=42)
    
    # 5. جستجوی تصادفی (Random Search)
    tscv = TimeSeriesSplit(n_splits=3)
    
    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_dist,
        n_iter=10, # تعداد تست‌ها (می‌توانید بیشتر کنید، مثلا 20)
        scoring='precision', 
        cv=tscv,
        verbose=1,
        n_jobs=-1
    )
    
    print("🚀 Tuning in progress... (This may take a few minutes)")
    search.fit(X, y)
    
    print("\n✅ Optimization Complete!")
    print(f"🏆 Best Precision Score: {search.best_score_:.2%}")
    print("🏆 Best Parameters:")
    print(search.best_params_)
    
    return search.best_params_

if __name__ == "__main__":
    run_tuning()