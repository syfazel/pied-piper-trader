# src/ui/worker.py
from PySide6.QtCore import QThread, Signal
import traceback
import asyncio
import pandas as pd
import numpy as np
import time # <--- FIX: اضافه شد

# ایمپورت ماژول‌های سیستم
from src.ingest.wallex import WallexConnector
from src.ingest.big_data import BigDataManager
from src.features.indicators import TechnicalFeatures
from src.strategy.scoring import SmartStrategy
from src.ml.ensemble import EnsemblePredictor
from src.ml.dataset import DataLabeler, SEQUENCE_LENGTH 
from src.nlp.sentiment import NewsAnalyzer
from src.reporting.generator import ReportGenerator
from src.core.persistence import DBManager 
from src.core.utils import LOGGER 
from src.core.doctor import SystemDoctor

class AnalysisWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)
    log = Signal(str)

    def __init__(self, symbol="ETHUSDT"):
        super().__init__()
        self.symbol = symbol
        self.doctor = SystemDoctor()

    def run(self):
        db_manager = DBManager()
        big_data_mgr = BigDataManager()
        start_time = time.time() # تایمر دکتر
        
        try:
            LOGGER.info("WORKER: Starting RAW analysis cycle...")
            
            # 1. دریافت داده زنده
            self.log.emit("📡 Fetching Live Data...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            live_df = loop.run_until_complete(self._fetch_data())
            loop.close()

            if live_df is None or live_df.empty: 
                raise Exception("Live data fetch failed.")
            
            current_price = live_df.iloc[-1]['close']

            # 2. ترکیب با داده‌های ۵۰ هزارتایی
            self.log.emit("💾 Merging Big Data...")
            full_df = big_data_mgr.get_combined_data(live_df, target_size=50000)

            # 3. محاسبه اندیکاتورها
            self.log.emit("⚙️ Calculating Indicators...")
            df_processed = TechnicalFeatures.add_all(full_df)

            # 4. هوش مصنوعی (بدون سانسور!)
            self.log.emit("🤖 AI: Analyzing (No Filter)...")
            labeler = DataLabeler()
            X, y, scaler = labeler.prepare(df_processed) 
            
            ensemble = EnsemblePredictor()
            ensemble.train_all(X, y) 
            
            # بررسی طول داده
            if len(X) < SEQUENCE_LENGTH:
                last_features = X
            else:
                last_features = X.tail(SEQUENCE_LENGTH)

            # پیش‌بینی خام (Raw Prediction)
            ai_pred, ai_conf = ensemble.predict_combined(last_features) 
            
            # محاسبه SHAP
            last_row_df = pd.DataFrame(X.tail(1), columns=X.columns)
            shap_importance = ensemble.aux_predictor.get_feature_importance(last_row_df)

            # 5. ثبت و اعتبارسنجی (بدون شرط اطمینان بالا)
            self.log.emit("⚖️ Recording Prediction...")
            db_manager.validate_past_predictions(current_price, validation_period_minutes=120)
            
            ai_direction = "BUY" if ai_pred == 1 else "SELL"
            
            # ذخیره همه پیش‌بینی‌ها (بدون فیلتر)
            db_manager.add_prediction(self.symbol, ai_direction, ai_conf, current_price)
            
            # 6. استراتژی و اخبار
            self.log.emit("🧠 Strategy & News...")
            strategy = SmartStrategy()
            
            connector = WallexConnector()
            macro_data = connector.get_macro_prices()
            
            nlp = NewsAnalyzer()
            sent_res = nlp.analyze_headlines() 
            
            recent_df = df_processed.tail(100)
            strat_res = strategy.analyze(recent_df, macro_data, sent_res['sentiment_score'])
            
            action_to_save = strat_res.get('signal', strat_res.get('action', 'UNKNOWN'))
            db_manager.save_signal(self.symbol, action_to_save, strat_res['score'], current_price)
            
            # 7. خروجی نهایی
            history_df, accuracy = db_manager.get_ai_history()
            
            report_text = ReportGenerator.create_report(
                self.symbol, strat_res, (ai_pred, ai_conf), sent_res, shap_importance
            )

            result_package = {
                "dataframe": recent_df, 
                "report": report_text, 
                "strategy": strat_res, 
                "sentiment": sent_res, 
                "macro": macro_data, 
                "history": {"df": history_df, "accuracy": accuracy},
                "feature_weights": shap_importance
            }
            
            # ثبت علائم حیاتی در دکتر
            self.doctor.checkup(start_time, (ai_pred, ai_conf), strat_res)
            
            self.finished.emit(result_package)

        except Exception as e:
            LOGGER.error(f"WORKER ERROR: {e}", exc_info=True)
            traceback.print_exc()
            self.error.emit(str(e))
        finally:
            db_manager.close() 

    async def _fetch_data(self):
        async with WallexConnector() as exchange:
            return await exchange.fetch_ohlcv(self.symbol, timeframe="1h", limit=2000)