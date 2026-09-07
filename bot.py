import requests
import pandas as pd
import numpy as np
import time
import yfinance as yf

# Внесете ги вашите податоци од BotFather и вашиот Chat ID
TOKEN = "ВАШИОТ_БОТ_ТОКЕН_ОД_БОТФАТЕР"
CHAT_ID = "ВАШИОТ_CHAT_ID"

ASSET_SYMBOL = "EURUSD=X"
ASSET_NAME = "EUR/USD"

def get_market_data():
    try:
        df = yf.download(ASSET_SYMBOL, period="2d", interval="5m", progress=False)
        if df.empty:
            return None
        df = df.dropna()
        return df
    except Exception as e:
        print(f"Грешка при симнување податоци: {e}")
        return None

def calculate_indicators(df):
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    low_min = df['low'].rolling(window=14).min()
    high_max = df['high'].rolling(window=14).max()
    df['Stoch_K'] = ((df['close'] - low_min) / (high_max - low_min)) * 100
    
    return df

def check_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    if pd.isna(last['SMA_50']) or pd.isna(last['RSI']) or pd.isna(last['Stoch_K']):
        return None
        
    if (last['close'] > last['SMA_50']) and (last['RSI'] < 35) and (prev['Stoch_K'] < 20 and last['Stoch_K'] > 20):
        return "КУПУВАЊЕ (CALL / HIGHER)"
    elif (last['close'] < last['SMA_50']) and (last['RSI'] > 65) and (prev['Stoch_K'] > 80 and last['Stoch_K'] < 80):
        return "ПРОДАЖБА (PUT / LOWER)"
        
    return None

def send_telegram_signal(action, price):
    emoji = "🟢" if "КУПУВАЊЕ" in action else "🔴"
    message = (
        f"{emoji} **БИНАРЕН СИГНАЛ (5 МИН)** {emoji}\n\n"
        f"📊 **Актив:** {ASSET_NAME}\n"
        f"📈 **Тип:** {action}\n"
        f"⏱ **Време на истек (Expiry):** 5 Минути\n"
        f"💲 **Цена на влезот:** {price:.5f}\n"
        f"⏰ **Време:** {time.strftime('%H:%M:%S %d-%m-%Y')}"
    )
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Мрежна грешка: {e}")

if __name__ == "__main__":
    print(f"Облак ботот за 5-минутни бинарни сигнали за {ASSET_NAME} е стартуван...")
    last_signal_time = None

    while True:
        df = get_market_data()
        if df is not None:
            df = calculate_indicators(df)
            current_bar_time = df.index[-1]
            signal = check_signal(df)
            
            if signal and current_bar_time != last_signal_time:
                current_price = float(df.iloc[-1]['close'])
                send_telegram_signal(signal, current_price)
                last_signal_time = current_bar_time
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Облак проверка... Нема нов услов.")
        
        time.sleep(60)
