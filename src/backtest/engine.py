# src/backtest/engine.py
import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital=1000, fee_rate=0.003):
        """
        :param initial_capital: سرمایه اولیه (دلار/تتر)
        :param fee_rate: نرخ کارمزد (0.003 = 0.3%)
        """
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.reset()

    def reset(self):
        self.balance = self.initial_capital  # پول نقد (USDT)
        self.position = 0.0                  # مقدار دارایی (ETH)
        self.trades = []                     # تاریخچه معاملات
        self.equity_curve = []               # نمودار دارایی در طول زمان

    def run(self, df: pd.DataFrame, strategy, macro_data=None):
        """
        اجرای بک‌تست روی داده‌های تاریخی
        """
        self.reset()
        print(f"🔄 Starting Backtest on {len(df)} candles...")

        for i in range(len(df)):
            # شبیه‌سازی داده تا لحظه i (جلوگیری از نگاه به آینده)
            # نکته: برای سرعت بالاتر در نسخه واقعی، اندیکاتورها از قبل محاسبه شده‌اند
            # و ما فقط ردیف i را میخوانیم.
            current_candle = df.iloc[i]
            current_price = current_candle['close']
            timestamp = current_candle.name if hasattr(current_candle, 'name') else df.index[i]
            
            # اجرای استراتژی روی داده‌های موجود تا این لحظه
            # ما کل DF را می‌فرستیم اما استراتژی فقط به iloc[-1] نگاه می‌کند
            # برای بک‌تست دقیق، باید برشی از DF تا زمان i را بفرستیم:
            # اما چون اندیکاتورها از قبل محاسبه شده‌اند (Shift نشده)،
            # ما فرض می‌کنیم df ورودی شامل ستون‌های سیگنال است یا استراتژی Stateless است.
            
            # تحلیل وضعیت فعلی (با فرض اینکه استراتژی روی یک ردیف کار می‌کند یا DF کامل دارد)
            # روش بهینه: ارسال برش کوچک نیست، بلکه خواندن سیگنال محاسبه شده است.
            # اینجا برای سادگی، استراتژی را روی یک اسلایس اجرا می‌کنیم (کندتر اما دقیق):
            slice_df = df.iloc[:i+1]
            if len(slice_df) < 50: continue # نیاز به دیتای کافی برای اندیکاتورها

            signal = strategy.analyze(slice_df, macro_data=macro_data)
            action = signal['action']

            # --- منطق اجرای ترید ---
            
            # خرید (اگر پول داریم و سیگنال خرید است)
            if "BUY" in action and self.balance > 10: # حداقل 10 دلار
                amount_to_buy = (self.balance * 0.98) / current_price # 98% موجودی را می‌خریم
                cost = amount_to_buy * current_price
                fee = cost * self.fee_rate
                
                self.balance -= (cost + fee)
                self.position += amount_to_buy
                
                self.trades.append({
                    'type': 'BUY',
                    'price': current_price,
                    'amount': amount_to_buy,
                    'time': timestamp,
                    'balance': self.balance
                })
            
            # فروش (اگر دارایی داریم و سیگنال فروش است)
            elif "SELL" in action and self.position > 0.001:
                revenue = self.position * current_price
                fee = revenue * self.fee_rate
                
                self.balance += (revenue - fee)
                self.position = 0
                
                self.trades.append({
                    'type': 'SELL',
                    'price': current_price,
                    'amount': 0, # همه را فروختیم
                    'time': timestamp,
                    'balance': self.balance
                })

            # محاسبه ارزش کل دارایی در این لحظه
            equity = self.balance + (self.position * current_price)
            self.equity_curve.append({'time': timestamp, 'equity': equity})

        return self.generate_report()

    def generate_report(self):
        """محاسبه شاخص‌های عملکرد (KPIs)"""
        df_equity = pd.DataFrame(self.equity_curve)
        if df_equity.empty: return "No trades executed."
        
        final_equity = df_equity.iloc[-1]['equity']
        total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        # محاسبه Max Drawdown
        df_equity['peak'] = df_equity['equity'].cummax()
        df_equity['drawdown'] = (df_equity['equity'] - df_equity['peak']) / df_equity['peak']
        max_drawdown = df_equity['drawdown'].min() * 100
        
        # محاسبه Win Rate
        wins = 0
        losses = 0
        # منطق ساده: مقایسه قیمت فروش با قیمت خرید قبلی
        for i in range(1, len(self.trades)):
            if self.trades[i]['type'] == 'SELL':
                buy_price = self.trades[i-1]['price']
                sell_price = self.trades[i]['price']
                if sell_price > buy_price: wins += 1
                else: losses += 1
        
        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0

        return {
            "Initial Capital": self.initial_capital,
            "Final Equity": round(final_equity, 2),
            "Total Return": f"{total_return:.2f}%",
            "Max Drawdown": f"{max_drawdown:.2f}%",
            "Total Trades": len(self.trades),
            "Win Rate": f"{win_rate:.1f}%",
            "Trade History": pd.DataFrame(self.trades)
        }