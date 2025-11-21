# src/nlp/sentiment.py
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib3
from src.core.utils import LOGGER

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NewsAnalyzer:
    def __init__(self):
        self.bullish_keywords = ['surge', 'jump', 'record', 'etf', 'approve', 'bull', 'gain', 'rally', 'high']
        self.bearish_keywords = ['crash', 'ban', 'hack', 'lawsuit', 'inflation', 'bear', 'drop', 'sell', 'low']
        
        # آدرس RSS واقعی
        self.rss_url = "https://cointelegraph.com/rss"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.proxies = {"http": None, "https": None}

    def analyze_headlines(self) -> dict:
        """
        دریافت اخبار واقعی. اگر خبری نبود، لیست خالی برمی‌گرداند (بدون فیک).
        """
        news_list = self.fetch_real_news()
        
        if not news_list:
            LOGGER.warning("NLP: No real news fetched. Returning empty list.")
            # --- تغییر مهم: دیگر خبری از simulate_data نیست ---
            news_list = [] 
            score = 50 # امتیاز خنثی وقتی خبری نیست
        else:
            score = 50
            for news in news_list:
                if news['sentiment'] == 'positive': score += 3
                elif news['sentiment'] == 'negative': score -= 3
            score = max(0, min(100, score))

        return {
            "sentiment_score": score,
            "news_count": len(news_list),
            "summary": "Real-time Analysis" if news_list else "No Connection / No News",
            "news_list": news_list
        }

    def fetch_real_news(self):
        try:
            # تایم‌اوت کم (5 ثانیه) تا اگر اینترنت قطع بود سریع رد شود و برنامه را کند نکند
            response = requests.get(self.rss_url, headers=self.headers, timeout=5, verify=False, proxies=self.proxies)
            if response.status_code != 200: return None
            
            root = ET.fromstring(response.content)
            news_items = []
            
            for item in root.findall('./channel/item')[:15]: # 15 خبر آخر
                title = item.find('title').text
                pub_date = item.find('pubDate').text
                
                try:
                    dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                    time_str = dt.strftime("%H:%M")
                except:
                    time_str = datetime.now().strftime("%H:%M")
                
                sentiment = 'neutral'
                t_lower = title.lower()
                if any(w in t_lower for w in self.bullish_keywords): sentiment = 'positive'
                elif any(w in t_lower for w in self.bearish_keywords): sentiment = 'negative'
                
                news_items.append({
                    'title': title, 
                    'source': 'CoinTelegraph', 
                    'time': time_str, 
                    'sentiment': sentiment
                })
            
            return news_items
        except Exception as e:
            LOGGER.error(f"NLP Error: {e}")
            return None