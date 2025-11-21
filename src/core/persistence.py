# src/core/persistence.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

DB_PATH = 'trader.db'

class DBManager:
    def __init__(self):
        # ایجاد اتصال و ایجاد فایل دیتابیس
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """ایجاد جداول signals و ai_history."""
        # 1. جدول ذخیره سیگنال‌های نهایی و امتیاز نهایی
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                final_action TEXT,
                final_score REAL,
                price REAL
            )
        """)
        
        # 2. جدول تاریخچه اعتبارسنجی AI (جایگزین ai_history.csv)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_history (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                predicted_direction TEXT,
                confidence REAL,
                entry_price REAL,
                status TEXT, -- PENDING, CORRECT, WRONG
                actual_result REAL
            )
        """)
        self.conn.commit()

    def save_signal(self, symbol, action, score, price):
        """ذخیره سیگنال نهایی تولید شده توسط StrategyEngine."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            INSERT INTO signals (timestamp, symbol, final_action, final_score, price)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, symbol, action, score, price))
        self.conn.commit()
        
    def add_prediction(self, symbol, direction, confidence, current_price):
        """ثبت یک پیش‌بینی جدید از AI."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cursor.execute("""
            INSERT INTO ai_history (timestamp, symbol, predicted_direction, confidence, entry_price, status, actual_result)
            VALUES (?, ?, ?, ?, ?, 'PENDING', 0.0)
        """, (timestamp, symbol, direction, confidence, current_price))
        self.conn.commit()

    def validate_past_predictions(self, current_price, validation_period_minutes=120):
        """بررسی پیش‌بینی‌های گذشته و به‌روزرسانی وضعیت (VALIDATION LOOP)."""
        validation_time = datetime.now() - timedelta(minutes=validation_period_minutes)
        validation_time_str = validation_time.strftime("%Y-%m-%d %H:%M")

        # گرفتن تمام پیش‌بینی‌های PENDING که زمان بررسی آن‌ها رسیده است
        self.cursor.execute("""
            SELECT id, predicted_direction, entry_price FROM ai_history 
            WHERE status = 'PENDING' AND timestamp <= ?
        """, (validation_time_str,))
        
        pending_trades = self.cursor.fetchall()
        
        for trade_id, direction, entry, in pending_trades:
            entry = float(entry)
            is_correct = False
            
            # Logic: Did the price move in the predicted direction?
            if direction == "BUY" and current_price > entry:
                is_correct = True
            elif direction == "SELL" and current_price < entry:
                is_correct = True

            status = 'CORRECT' if is_correct else 'WRONG'
            
            self.cursor.execute("""
                UPDATE ai_history SET status = ?, actual_result = ? 
                WHERE id = ?
            """, (status, current_price, trade_id))
            
        self.conn.commit()

    def get_ai_history(self):
        """دریافت کل تاریخچه AI برای نمایش در UI."""
        df = pd.read_sql_query("SELECT * FROM ai_history ORDER BY id DESC", self.conn)
        
        # محاسبه دقت
        finished = df[df['status'] != 'PENDING']
        if finished.empty: 
            accuracy = 0.0
        else:
            correct = len(finished[finished['status'] == 'CORRECT'])
            total = len(finished)
            accuracy = (correct / total) * 100
            
        return df, accuracy
        
    def close(self):
        self.conn.close()