# src/strategy/scoring.py
import pandas as pd

class SmartStrategy:
    """
    موتور تصمیم‌گیری هوشمند (نسخه استاندارد - بدون کوانتوم).
    """
    def analyze(self, df: pd.DataFrame, macro_data: dict = None, sentiment_score: float = 50) -> dict:
        if df is None or df.empty:
            return {"action": "WAIT", "score": 0, "reasons": [], "signal": "WAIT", "color": "#888"}
            
        current = df.iloc[-1]
        reasons = []
        tech_score = 50
        
        # 1. تحلیل تکنیکال
        if current['rsi'] < 30:
            tech_score += 20
            reasons.append(f"Oversold RSI ({current['rsi']:.0f})")
        elif current['rsi'] > 70:
            tech_score -= 20
            reasons.append(f"Overbought RSI ({current['rsi']:.0f})")
            
        if current['macd_hist'] > 0:
            tech_score += 10
        else:
            tech_score -= 5
            
        # 2. تحلیل ماکرو (تومانی)
        macro_score = 50
        if macro_data:
            usdt_tmn = macro_data.get('USDT_IRT', 0)
            gold_tmn = macro_data.get('GOLD_IRT', 0)
            
            if usdt_tmn > 65000:
                macro_score += 15
                reasons.append(f"High USD Rate ({usdt_tmn:,.0f})")
            
            if gold_tmn > 180000000:
                macro_score += 10
                reasons.append("Gold Support")

        # 3. محاسبه امتیاز نهایی (بدون کوانتوم)
        # وزن‌ها را دوباره تنظیم می‌کنیم تا به 100 برسد
        # تکنیکال: 50% | ماکرو: 30% | اخبار کلاسیک: 20%
        final_score = (
            (0.5 * tech_score) + 
            (0.3 * macro_score) + 
            (0.2 * sentiment_score)
        )
        
        # تصمیم‌گیری
        action = "HOLD"
        color = "#FFFFFF"
        
        if final_score >= 60:
            action = "BUY"
            color = "#00E676"
        elif final_score <= 40:
            action = "SELL"
            color = "#FF5252"
        
        return {
            "symbol": "Unknown",
            "signal": action,
            "action": action,
            "score": round(final_score, 1),
            "reasons": reasons,
            "color": color,
            "price": current['close']
        }