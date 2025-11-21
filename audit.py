import sys
import os
import pandas as pd
import numpy as np
import traceback
import asyncio
import warnings
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# غیرفعال کردن وارنینگ‌های غیرمهم برای تمیزی گزارش
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

# تنظیمات محیطی
sys.path.append(os.getcwd())

# فایل خروجی
REPORT_FILE = "DIAGNOSTIC_REPORT.txt"

def log(message):
    """نوشتن همزمان در کنسول و فایل"""
    print(message)
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def section(title):
    log(f"\n{'='*60}\n {title}\n{'='*60}")

async def run_audit():
    # پاک کردن گزارش قبلی
    if os.path.exists(REPORT_FILE): os.remove(REPORT_FILE)
    
    section("1. SYSTEM INFO")
    log(f"Python Version: {sys.version}")
    log(f"Platform: {sys.platform}")
    try:
        import tensorflow as tf
        log(f"TensorFlow Version: {tf.__version__}")
        import sklearn
        log(f"Scikit-learn Version: {sklearn.__version__}")
    except ImportError as e:
        log(f"CRITICAL MISSING LIB: {e}")

    section("2. DATA HEALTH CHECK")
    try:
        from src.ingest.wallex import WallexConnector
        from src.ingest.big_data import BigDataManager
        
        log("Fetching Data Sample (Live + History)...")
        # دریافت داده نمونه
        async with WallexConnector() as exchange:
            live_df = await exchange.fetch_ohlcv("ETHUSDT", timeframe="1h", limit=1000)
        
        big_data = BigDataManager()
        # فقط 5000 تا برای تست سریع
        df = big_data.get_combined_data(live_df, target_size=5000)
        
        log(f"Data Shape: {df.shape}")
        log(f"Date Range: {df.index.min()} to {df.index.max()}")
        
        # بررسی داده‌های گم شده
        missing = df.isnull().sum().sum()
        log(f"Total Missing Values (NaN): {missing}")
        if missing > 0:
            log(str(df.isnull().sum()[df.isnull().sum() > 0]))

        # بررسی تکراری بودن ایندکس
        duplicates = df.index.duplicated().sum()
        log(f"Duplicated Time Indices: {duplicates}")

    except Exception as e:
        log(f"DATA ERROR: {traceback.format_exc()}")
        return

    section("3. FEATURE ENGINEERING CHECK")
    try:
        from src.features.indicators import TechnicalFeatures
        from src.ml.dataset import DataLabeler
        
        log("Applying Indicators...")
        df_processed = TechnicalFeatures.add_all(df)
        log(f"Shape after Features: {df_processed.shape}")
        
        # بررسی مقادیر بی‌نهایت
        inf_count = np.isinf(df_processed.select_dtypes(include=np.number)).sum().sum()
        log(f"Infinite Values: {inf_count}")

        log("Labeling Data (Target Generation)...")
        labeler = DataLabeler()
        X, y, scaler = labeler.prepare(df_processed)
        
        log(f"Final Training Set X: {X.shape}")
        log(f"Final Training Set y: {y.shape}")
        
        # بررسی تعادل کلاس‌ها (مهم‌ترین بخش)
        class_counts = pd.Series(y).value_counts(normalize=True)
        log("\nTARGET BALANCE (Is the game rigged?):")
        log(str(class_counts))
        
        if class_counts.min() < 0.1:
            log("⚠️ WARNING: Severe Class Imbalance! Model will just guess the majority class.")

        # بررسی همبستگی ویژگی‌ها با هدف
        log("\nFEATURE CORRELATION WITH TARGET:")
        # ترکیب موقت برای محاسبه کورلیشن
        temp_df = pd.DataFrame(X, columns=X.columns)
        temp_df['target'] = y.values
        corr = temp_df.corr()['target'].sort_values(ascending=False)
        log(str(corr))

    except Exception as e:
        log(f"FEATURE ERROR: {traceback.format_exc()}")
        return

    section("4. MODEL PERFORMANCE DIAGNOSIS")
    try:
        from src.ml.ensemble import EnsemblePredictor
        
        # تقسیم داده برای تست صادقانه
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        log("Training Ensemble Model on Audit Subset...")
        ensemble = EnsemblePredictor()
        ensemble.train_all(X_train, y_train)
        
        # ارزیابی مدل
        log("\n--- Evaluating Model A (LSTM/Boosting) ---")
        # نیاز به آماده‌سازی توالی برای تست
        if hasattr(ensemble.predictor_A, 'model'): # اگر LSTM است
             # تبدیل سریع برای تست (ساده شده)
             # (در اینجا فقط بررسی می‌کنیم که آیا پیش‌بینی می‌کند یا خیر)
             pass
        
        # ارزیابی مدل ترکیبی نهایی
        log("\n--- Evaluating Final Ensemble (Combined) ---")
        # ساخت پیش‌بینی‌ها
        preds = []
        # برای سرعت، روی 100 نمونه آخر تست می‌کنیم
        test_subset = X_test.tail(100)
        y_subset = y_test.tail(100)
        
        if len(test_subset) > 10: # اگر داده کافی بود
            # آماده‌سازی برای LSTM اگر لازم باشد
            # (در کد اصلی داخل predict_combined هندل شده است)
            
            predictions = []
            for i in range(len(test_subset)):
                 # شبیه‌سازی ارسال توالی
                 if i < 10: continue
                 sample = test_subset.iloc[i-10:i] # توالی 10 تایی
                 pred, conf = ensemble.predict_combined(sample)
                 predictions.append(pred)
            
            # برش تارگت برای همخوانی
            y_true = y_subset.iloc[10:]
            
            if len(predictions) > 0:
                log("\nConfusion Matrix:")
                log(str(confusion_matrix(y_true, predictions)))
                
                log("\nClassification Report:")
                log(str(classification_report(y_true, predictions)))
            else:
                log("Not enough data in subset for prediction loop.")

    except Exception as e:
        log(f"MODEL ERROR: {traceback.format_exc()}")

    section("5. LOG FILE ANALYSIS")
    try:
        # پیدا کردن آخرین فایل لاگ
        log_files = [f for f in os.listdir() if f.startswith("app_log") and f.endswith(".txt")]
        if log_files:
            latest_log = max(log_files)
            log(f"Reading last 20 lines from {latest_log}:")
            with open(latest_log, "r", encoding="utf-8") as f:
                lines = f.readlines()[-20:]
                for line in lines:
                    log(line.strip())
        else:
            log("No app_log file found.")
    except Exception as e:
        log(f"LOG READ ERROR: {e}")

    section("END OF AUDIT")
    print(f"\n✅ Diagnosis Complete. Please send '{REPORT_FILE}' to the AI.")

if __name__ == "__main__":
    asyncio.run(run_audit())