# src/reporting/scientific.py
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os

class ScientificReporter:
    def __init__(self, db_path='trader.db'):
        self.db_path = db_path

    def generate_full_report(self):
        if not os.path.exists(self.db_path):
            return "Database not found.", "Error"

        conn = sqlite3.connect(self.db_path)
        try:
            signals_df = pd.read_sql_query("SELECT * FROM signals", conn)
            ai_df = pd.read_sql_query("SELECT * FROM ai_history", conn)
        except Exception as e:
            return f"DB Error: {e}", "Error"
        finally:
            conn.close()

        # --- FIX: منطق شمارش صحیح ---
        total_signals = len(signals_df)
        
        # تبدیل به حروف بزرگ و حذف فاصله‌های اضافی برای شمارش دقیق
        if not signals_df.empty:
            actions = signals_df['final_action'].str.upper().str.strip()
            
            # شمارش دقیق کلمات کلیدی
            buy_signals = actions[actions.str.contains('BUY')].count()
            sell_signals = actions[actions.str.contains('SELL')].count()
            # هر چیزی که خرید یا فروش نیست، Wait است
            wait_signals = total_signals - (buy_signals + sell_signals)
        else:
            buy_signals, sell_signals, wait_signals = 0, 0, 0

        # آمار هوش مصنوعی (بدون تغییر)
        ai_validated = ai_df[ai_df['status'].isin(['CORRECT', 'WRONG'])]
        ai_correct = len(ai_validated[ai_validated['status'] == 'CORRECT'])
        ai_total_val = len(ai_validated)
        ai_precision = (ai_correct / ai_total_val * 100) if ai_total_val > 0 else 0

        # تولید گزارش
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_content = f"""
================================================================
          🔬 PIED PIPER: CORRECTED DIAGNOSTIC REPORT
================================================================
Date: {timestamp}

1. REALITY CHECK (Signals)
---------------------------
- Total Cycles: {total_signals}
- BUY  Signals: {buy_signals}
- SELL Signals: {sell_signals}
- WAIT Signals: {wait_signals}
* Note: If BUY is 0 but CSV has BUYS, check database integrity.

2. AI PERFORMANCE
---------------------------
- Precision (Real Accuracy): {ai_precision:.2f}%
- Validated Samples: {ai_total_val}

================================================================
"""
        filename = f"Scientific_Report_FIXED.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        return filename, report_content