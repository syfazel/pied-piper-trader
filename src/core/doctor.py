# src/core/doctor.py
import psutil
import time
import pandas as pd
import os
from datetime import datetime

class SystemDoctor:
    def __init__(self, report_file="doctor_report.csv"):
        self.report_file = report_file
        self.start_time = time.time()
        
        # اگر فایل نبود، سرستون‌ها را بساز
        if not os.path.exists(self.report_file):
            df = pd.DataFrame(columns=[
                "timestamp", "uptime_min", 
                "cpu_percent", "ram_mb", 
                "api_latency_ms", "cycle_duration_s",
                "ai_confidence", "ai_signal", 
                "strategy_score"
            ])
            df.to_csv(self.report_file, index=False)

    def checkup(self, api_start_time, ai_result, strat_result):
        """
        این متد در پایان هر چرخه تحلیل صدا زده می‌شود تا وضعیت را ثبت کند.
        """
        # 1. زمان و آپتایم
        now = datetime.now()
        uptime = (time.time() - self.start_time) / 60 # دقیقه
        
        # 2. وضعیت سخت‌افزار (Vital Signs)
        cpu = psutil.cpu_percent(interval=None)
        process = psutil.Process(os.getpid())
        ram = process.memory_info().rss / 1024 / 1024 # تبدیل به مگابایت
        
        # 3. سرعت شبکه و پردازش (Performance)
        cycle_end_time = time.time()
        # api_start_time زمانی است که درخواست به والکس فرستاده شد
        # latency = کل زمانی که طول کشید تا چرخه تمام شود
        duration = cycle_end_time - api_start_time
        
        # 4. وضعیت مغز هوش مصنوعی (Brain Health)
        ai_conf = ai_result[1] if ai_result else 0
        ai_sig = "BUY" if ai_result[0] == 1 else "SELL"
        score = strat_result.get('score', 0)

        # 5. ثبت در پرونده پزشکی
        new_record = {
            "timestamp": now.strftime("%H:%M:%S"),
            "uptime_min": round(uptime, 1),
            "cpu_percent": cpu,
            "ram_mb": round(ram, 1),
            "api_latency_ms": round(duration * 1000, 0), # میلی‌ثانیه
            "cycle_duration_s": round(duration, 2),
            "ai_confidence": round(ai_conf * 100, 1),
            "ai_signal": ai_sig,
            "strategy_score": score
        }
        
        df = pd.DataFrame([new_record])
        df.to_csv(self.report_file, mode='a', header=False, index=False)
        
        return new_record