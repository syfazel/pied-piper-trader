# tools/miner.py
import requests
import pandas as pd
import time
import os
from datetime import datetime

# --- تنظیمات دقیق برای تومان ---
SYMBOL = "ETHTMN"  # <--- مهم: حتما باید ETHTMN باشد
TIMEFRAME = "60"
TARGET_CANDLES = 50000
BATCH_SIZE = 500 
OUTPUT_FILE = "data/history_50k.csv"

def fetch_batch(to_timestamp):
    url = "https://api.wallex.ir/v1/udf/history"
    from_timestamp = to_timestamp - (BATCH_SIZE * 60 * 60)
    
    params = {
        'symbol': SYMBOL,
        'resolution': TIMEFRAME,
        'from': from_timestamp,
        'to': to_timestamp
    }
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()
        if data['s'] == 'ok':
            df = pd.DataFrame({
                'timestamp': data['t'],
                'open': data['o'], 'high': data['h'], 
                'low': data['l'], 'close': data['c'], 'volume': data['v']
            })
            return df
    except:
        pass
    return None

def mine_data():
    if not os.path.exists("data"): os.makedirs("data")
    
    # حذف فایل قبلی (چه دلاری، چه مصنوعی)
    if os.path.exists(OUTPUT_FILE): 
        print("🗑️ Deleting old file to start fresh...")
        os.remove(OUTPUT_FILE)
    
    all_dfs = []
    current_end = int(time.time())
    collected = 0
    
    print(f"⛏️ MINING STARTED: Fetching {TARGET_CANDLES} candles for {SYMBOL}...")
    
    while collected < TARGET_CANDLES:
        df = fetch_batch(current_end)
        
        if df is None or df.empty:
            print("❌ End of data reached.")
            break
            
        cols = ['open', 'high', 'low', 'close', 'volume']
        df[cols] = df[cols].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        
        all_dfs.append(df)
        collected += len(df)
        
        last_price = df.iloc[-1]['close']
        # نمایش قیمت برای اطمینان (باید میلیونی باشد)
        print(f"   ✅ Got {len(df)} | Total: {collected} | Price: {last_price:,.0f} T")
        
        first_time = df.index.min().timestamp()
        current_end = int(first_time) - 1
        time.sleep(0.2)

    if all_dfs:
        print("💾 Saving real Toman data...")
        final_df = pd.concat(all_dfs)
        final_df.sort_index(inplace=True)
        final_df = final_df[~final_df.index.duplicated(keep='first')]
        final_df.to_csv(OUTPUT_FILE)
        print(f"🎉 SUCCESS! Saved {len(final_df)} real Toman candles.")
    else:
        print("❌ Failed.")

if __name__ == "__main__":
    mine_data()