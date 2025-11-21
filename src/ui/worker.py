# src/ui/worker.py
from PySide6.QtCore import QThread, Signal
import traceback
import asyncio
import pandas as pd
import numpy as np
import time
import gc
import os

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
    data_ready = Signal(dict)
    error = Signal(str)
    log = Signal(str)

    def __init__(self, symbol="ETHTMN"): # پیش‌فرض صحیح
        super().__init__()
        self.symbol = symbol
        self.doctor = SystemDoctor()
        self.is_running = True 
        self.ensemble = None 

    def stop(self):
        self.is_running = False

    def run(self):
        db_manager = DBManager()
        big_data_mgr = BigDataManager()
        
        LOGGER.info("WORKER: Initializing AI Brain...")
        self.log.emit("🚀 Initializing AI Engine...")
        
        if self.ensemble is None:
            self.ensemble = EnsemblePredictor()
        
        LOGGER.info("WORKER: Entering Infinite Monitoring Loop...")
        
        while self.is_running:
            loop_start = time.time()
            
            try:
                # --- FIX: اجبار به نماد صحیح تومانی ---
                if "USDT" in self.symbol and "TMN" not in self.symbol:
                     self.symbol = "ETHTMN" # تصحیح خودکار

                # 1. دریافت داده زنده
                self.log.emit(f"📡 Fetching Data ({self.symbol})...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                live_df = loop.run_until_complete(self._fetch_data())
                loop.close()

                if live_df is None or live_df.empty: 
                    self.log.emit("⚠️ Data Fetch Failed. Retrying...")
                    time.sleep(5)
                    continue
                
                current_price = live_df.iloc[-1]['close']

                # --- FIX: گارد امنیتی قیمت صفر ---
                if current_price <= 0:
                    LOGGER.error(f"CRITICAL: Received Zero Price for {self.symbol}. Market Offline?")
                    self.log.emit("⛔ Market Data Error (Price=0)")
                    time.sleep(5)
                    continue

                # 2. ترکیب داده‌ها
                full_df = big_data_mgr.get_combined_data(live_df, target_size=50000)
                
                # 3. پردازش (روی 2000 تای آخر برای سرعت)
                processing_df = full_df.tail(2000).copy()
                self.log.emit("⚙️ Analyzing...")
                df_processed = TechnicalFeatures.add_all(processing_df)

                # 4. هوش مصنوعی
                labeler = DataLabeler()
                X, y, scaler = labeler.prepare(df_processed) 
                
                if not self.ensemble.is_trained:
                    self.log.emit("🧠 First-time Training...")
                    self.ensemble.train_all(X, y)
                
                if len(X) < SEQUENCE_LENGTH:
                     raise Exception("Insufficient data buffer.")

                last_features = X.tail(SEQUENCE_LENGTH)
                
                # پیش‌بینی
                ai_pred_raw, ai_conf = self.ensemble.predict_combined(last_features) 
                
                # منطق سه وضعیتی
                THRESHOLD_BUY = 0.55
                THRESHOLD_SELL = 0.45
                
                if ai_conf >= THRESHOLD_BUY:
                    ai_direction = "BUY"
                elif ai_conf <= THRESHOLD_SELL:
                    ai_direction = "SELL"
                else:
                    ai_direction = "WAIT"

                # SHAP
                last_row_df = X.tail(1)
                shap_importance = self.ensemble.aux_predictor.get_feature_importance(last_row_df)

                # 5. اعتبارسنجی و ذخیره
                db_manager.validate_past_predictions(current_price, validation_period_minutes=120)
                
                if ai_direction != "WAIT":
                    db_manager.add_prediction(self.symbol, ai_direction, ai_conf, current_price)
                
                # 6. استراتژی و اخبار
                strategy = SmartStrategy()
                connector = WallexConnector()
                macro_data = connector.get_macro_prices()
                nlp = NewsAnalyzer()
                sent_res = nlp.analyze_headlines() 
                
                strat_res = strategy.analyze(df_processed.tail(100), macro_data, sent_res['sentiment_score'])
                
                # Consensus
                final_consensus = "WAIT"
                if strat_res['action'] == "BUY" and ai_direction == "BUY":
                    final_consensus = "BUY"
                elif strat_res['action'] == "SELL" and ai_direction == "SELL":
                    final_consensus = "SELL"
                
                db_manager.save_signal(self.symbol, final_consensus, strat_res['score'], current_price)
                
                # 7. ارسال نتیجه
                history_df, accuracy = db_manager.get_ai_history()
                
                # تبدیل برای گزارش
                ai_pred_code = 1 if ai_direction == "BUY" else 0
                
                report_text = ReportGenerator.create_report(
                    self.symbol, strat_res, (ai_pred_code, ai_conf), sent_res, shap_importance
                )

                result_package = {
                    "dataframe": df_processed.tail(150), 
                    "report": report_text, 
                    "strategy": strat_res, 
                    "sentiment": sent_res, 
                    "macro": macro_data, 
                    "history": {"df": history_df, "accuracy": accuracy},
                    "feature_weights": shap_importance
                }
                
                # ارسال وضعیت به دکتر
                strat_res_for_doctor = strat_res.copy()
                strat_res_for_doctor['action'] = final_consensus
                
                # اینجا ai_direction را می‌فرستیم (BUY/SELL/WAIT)
                self.doctor.checkup(loop_start, (ai_direction, ai_conf), strat_res_for_doctor)
                
                self.data_ready.emit(result_package)
                LOGGER.info(f"CYCLE DONE. Signal: {final_consensus} | AI: {ai_direction} ({ai_conf:.1%})")

                # پاکسازی حافظه
                del df_processed, X, y, full_df
                gc.collect()

            except Exception as e:
                LOGGER.error(f"CYCLE ERROR: {e}", exc_info=True)
                self.log.emit(f"⚠️ Error: {str(e)[:30]}...")
                time.sleep(5)

            for _ in range(5): 
                if not self.is_running: break
                time.sleep(1)
        
        db_manager.close()
        LOGGER.info("WORKER: Stopped.")

    async def _fetch_data(self):
        async with WallexConnector() as exchange:
            return await exchange.fetch_ohlcv(self.symbol, timeframe="1h", limit=2000)