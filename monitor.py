import time
import pandas as pd
import psutil
import requests
import os
from datetime import datetime, timedelta
import colorama
from colorama import Fore, Style

# تنظیمات اولیه
colorama.init(autoreset=True)
TARGET_CSV = "doctor_report.csv"
BENCHMARK_API = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
MEMORY_THRESHOLD = 85.0  # درصد هشدار رم
FREEZE_THRESHOLD_SEC = 120  # اگر سیستم ۲ دقیقه کاری نکرد، یعنی فریز شده

class ShadowMonitor:
    def __init__(self):
        self.last_known_price = 0
        print(f"{Fore.CYAN}--- SHADOW MONITOR INITIALIZED ---")
        print(f"{Fore.CYAN}--- Monitoring: {TARGET_CSV} ---")

    def technician_pulse_check(self):
        """بررسی حیاتی: آیا سیستم زنده است؟"""
        try:
            # 1. بررسی وجود فایل
            if not os.path.exists(TARGET_CSV):
                return False, "FILE_MISSING"

            # 2. بررسی آخرین آپدیت فایل (تشخیص فریز شدن)
            file_mod_time = os.path.getmtime(TARGET_CSV)
            time_diff = time.time() - file_mod_time
            
            if time_diff > FREEZE_THRESHOLD_SEC:
                return False, f"SYSTEM_FREEZE (Last update: {int(time_diff)}s ago)"

            # 3. بررسی مصرف منابع (RAM)
            ram_usage = psutil.virtual_memory().percent
            if ram_usage > MEMORY_THRESHOLD:
                return False, f"MEMORY_LEAK (RAM: {ram_usage}%)"

            return True, "SYSTEM_HEALTHY"
        except Exception as e:
            return False, f"TECH_ERROR: {str(e)}"

    def engineer_benchmark(self, internal_signal):
        """بررسی مهندسی: مقایسه با بازار جهانی"""
        try:
            # دریافت قیمت زنده از بایننس
            response = requests.get(BENCHMARK_API, timeout=5)
            data = response.json()
            current_price = float(data['price'])
            
            trend = "NEUTRAL"
            if self.last_known_price > 0:
                if current_price > self.last_known_price:
                    trend = "BULLISH"
                elif current_price < self.last_known_price:
                    trend = "BEARISH"
            
            self.last_known_price = current_price
            
            # تحلیل تطابق
            match_status = "NORMAL"
            if internal_signal == "BUY" and trend == "BEARISH":
                match_status = "CONTRARIAN_RISK" # خرید در بازار نزولی
            elif internal_signal == "SELL" and trend == "BULLISH":
                match_status = "CONTRARIAN_RISK" # فروش در بازار صعودی
                
            return current_price, trend, match_status
        except:
            return 0, "OFFLINE", "UNKNOWN"

    def doctor_audit(self):
        """بررسی دکتر: تحلیل منطق و هوش مصنوعی"""
        tech_ok, tech_msg = self.technician_pulse_check()
        
        if not tech_ok:
            print(f"{Fore.RED}🚨 [TECHNICIAN ALERT]: {tech_msg}")
            return

        try:
            # خواندن آخرین وضعیت ربات
            df = pd.read_csv(TARGET_CSV)
            if df.empty: return
            
            last_row = df.iloc[-1]
            ai_conf = float(last_row.get('ai_confidence', 0))
            ai_sig = str(last_row.get('ai_signal', 'WAIT'))
            
            # بررسی بنچمارک (مهندس)
            market_price, market_trend, conflict = self.engineer_benchmark(ai_sig)
            
            # --- چاپ گزارش وضعیت ---
            print("\n" + "="*50)
            print(f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}")
            
            # گزارش تکنسین
            print(f"👮 Technician: {Fore.GREEN}System Active{Style.RESET_ALL} | RAM: {psutil.virtual_memory().percent}%")
            
            # گزارش مهندس
            color_trend = Fore.GREEN if market_trend == "BULLISH" else Fore.RED
            print(f"👷 Engineer: Market is {color_trend}{market_trend}{Style.RESET_ALL} (Price: {market_price})")
            if conflict == "CONTRARIAN_RISK":
                print(f"{Fore.YELLOW}⚠️ WARNING: Robot is trading against the market trend!")
            
            # گزارش دکتر (تشخیص باگ)
            print(f"👨‍⚕️ Doctor Audit:")
            print(f"   - Robot Signal: {ai_sig}")
            print(f"   - Confidence: {ai_conf}%")
            
            # تشخیص باگ ۵۰ درصد
            if ai_conf == 50.0:
                print(f"{Fore.RED}   ❌ CRITICAL DIAGNOSIS: '50% BUG' DETECTED.")
                print(f"{Fore.RED}      The AI is uncertain but might be executing trades.")
            elif ai_conf < 55 and ai_sig != "WAIT":
                 print(f"{Fore.YELLOW}   ⚠️ RISK ALERT: Trading with low confidence (<55%)")
            else:
                print(f"{Fore.GREEN}   ✅ Logic seems healthy.")
                
        except Exception as e:
            print(f"{Fore.RED}❌ MONITOR CRASHED: {e}")

# اجرای لوپ مانیتورینگ
if __name__ == "__main__":
    monitor = ShadowMonitor()
    while True:
        monitor.doctor_audit()
        time.sleep(10) # هر ۱۰ ثانیه چک کن