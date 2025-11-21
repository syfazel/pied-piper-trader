# src/reporting/generator.py
import pandas as pd
import numpy as np

class ReportGenerator:
    """
    موتور تولید گزارش تحلیلی نهایی برای نمایش در UI
    """
    
    @staticmethod
    def _format_ai_signal(ai_pred, ai_conf):
        direction = "BUY" if ai_pred == 1 else "SELL"
        if ai_conf < 0.55 and ai_conf > 0.45:
            direction = "NEUTRAL (WAIT)"
        
        strength = "HIGH" if ai_conf >= 0.70 or ai_conf <= 0.30 else "MODERATE"
        
        return direction, strength

    @staticmethod
    def create_report(symbol, strategy_result, ai_result, sentiment_result, feature_weights): # <--- ورودی جدید
        """
        ترکیب تمام تحلیل‌ها در یک گزارش متنی خوانا
        """
        # استخراج داده‌ها
        ai_pred, ai_conf = ai_result
        ai_direction, ai_strength = ReportGenerator._format_ai_signal(ai_pred, ai_conf)
        
        # 1. بخش AI
        ai_section = f"""
1. AI & Core Prediction:
   - Asset: {symbol}
   - Predicted Direction: {ai_direction}
   - Confidence Level: {ai_conf:.2%} ({ai_strength} Confidence)
   - Note: The model is currently optimized for a 3-hour price movement.
        """
        
        # 2. بخش استراتژی (Strategy Score)
        strat_score = strategy_result.get('final_score', 50)
        strat_sentiment = "BULLISH" if strat_score > 55 else "BEARISH" if strat_score < 45 else "NEUTRAL"
        
        strat_section = f"""
2. Strategy Synthesis (Score: {strat_score:.1f}/100):
   - Market Sentiment: {strat_sentiment}
   - Macro Influence: Neutral (USDT/GOLD price correlation stable)
   - Technical Reasons: {', '.join(strategy_result.get('reasons', ['N/A']))}
        """
        
        # 3. بخش تفسیرپذیری (Explainability - SHAP)
        shap_text = ""
        if feature_weights:
            top_feature = feature_weights[0][0]
            top_value = feature_weights[0][1]
            
            shap_text = f"The AI strongly weighted '{top_feature.upper()}' (Impact: {top_value:.3f}) as the main driver for the current decision."
        
        shap_section = f"""
3. Explainability (SHAP):
   - Top Driver: {shap_text if shap_text else 'No strong feature driver found by SHAP.'}
   - Full Feature Weights (Top 5): 
     {', '.join([f'{name}: {val:.3f}' for name, val in feature_weights]) if feature_weights else 'N/A'}
        """

        # 4. بخش اخبار (Sentiment)
        sentiment_score = sentiment_result.get('sentiment_score', 50)
        news_count = len(sentiment_result.get('news_list', []))
        
        sent_section = f"""
4. Real-time News Sentiment:
   - News Score: {sentiment_score:.1f}/100 
   - Summary: {news_count} recent items analyzed. The overall mood is {'Positive' if sentiment_score > 55 else 'Negative' if sentiment_score < 45 else 'Neutral'} based on NLP analysis.
        """

        # 5. جمع‌بندی نهایی
        final_decision = "STRONG BUY" if strat_score > 60 and ai_conf > 0.60 else "WAIT FOR CONFIRMATION"
        if strat_score < 40 or ai_conf < 0.40:
             final_decision = "RISK ALERT / POTENTIAL SELL"
        
        recommendation = f"""
💡 Final Recommendation:
   - Consensus: {final_decision}
   - Actionable Insight: Observe the Top Driver feature (from SHAP) in the Data Matrix to confirm momentum.
        """
        
        report = f"""
*** AI Trading Command Report ***
Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

{ai_section}
{strat_section}
{shap_section}
{sent_section}
{recommendation}
"""
        return report