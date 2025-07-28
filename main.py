import yfinance as yf
import pandas as pd
import time
import requests

TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def fetch_signals(symbol):
    df = yf.download(f"{symbol}.NS", interval="5m", period="1d")
    if df is None or df.empty:
        return None

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["RSI"] = 100 - (100 / (1 + df["Close"].pct_change().rolling(14).mean() / df["Close"].pct_change().rolling(14).std()))
    df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()

    latest = df.iloc[-1]

    if latest["EMA20"] > latest["EMA50"] and latest["RSI"] < 70:
        return f"🔔 Buy Signal: {symbol}\nPrice: {latest['Close']:.2f}\nRSI: {latest['RSI']:.2f}"
    elif latest["EMA20"] < latest["EMA50"] and latest["RSI"] > 30:
        return f"⚠️ Sell Signal: {symbol}\nPrice: {latest['Close']:.2f}\nRSI: {latest['RSI']:.2f}"
    return None

nifty_50 = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "SBIN", "HINDUNILVR",
    "ITC", "LT", "AXISBANK", "ASIANPAINT", "HCLTECH", "BAJFINANCE", "WIPRO", "BHARTIARTL",
    "MARUTI", "SUNPHARMA", "NESTLEIND", "ULTRACEMCO", "POWERGRID", "NTPC", "COALINDIA",
    "TECHM", "HINDALCO", "TITAN", "GRASIM", "DIVISLAB", "BAJAJ-AUTO", "CIPLA", "HEROMOTOCO",
    "SBILIFE", "ADANIPORTS", "UPL", "BPCL", "ONGC", "JSWSTEEL", "DRREDDY", "EICHERMOT",
    "BRITANNIA", "INDUSINDBK", "HDFCLIFE", "TATACONSUM", "BAJAJFINSV", "TATASTEEL", "APOLLOHOSP",
    "SHREECEM", "M&M", "ICICIPRULI"
]

while True:
    for stock in nifty_50:
        try:
            signal = fetch_signals(stock)
            if signal:
                send_telegram_alert(signal)
        except Exception as e:
            print(f"Error checking {stock}: {e}")
    time.sleep(180)  # Wait for 3 minutes
