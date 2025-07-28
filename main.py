import pandas as pd
import time
import datetime
import requests

TELEGRAM_TOKEN = "8442847370:AAFMIHvOZGxiq5vl_x4W5inoqAhCQEwIzWk"
CHAT_ID = "617374916"
TWELVEDATA_API_KEY = "48c6e402d8bb4acb887b040a3c8a4f822"  # Replace with your actual TwelveData API key

entry_prices = {}  # Track entry prices for stocks

TARGET_PERCENT = 0.02  # 2% target
STOPLOSS_PERCENT = 0.01  # 1% stop-loss

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def fetch_intraday_data(symbol):
    try:
        symbol = symbol + ".NS"
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=30&apikey={TWELVEDATA_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if "values" not in data:
            print(f"No data for {symbol}")
            return None

        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df["Close"] = pd.to_numeric(df["close"])
        return df.sort_index()
    except Exception as e:
        print(f"❌ Failed to fetch {symbol}: {e}")
        return None

def compute_indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["Return"] = df["Close"].pct_change()
    df["RSI"] = 100 - (100 / (1 + df["Return"].rolling(14).mean() / df["Return"].rolling(14).std()))
    df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    return df

def fetch_signals(symbol):
    df = fetch_intraday_data(symbol)
    if df is None or df.empty:
        return None

    df = compute_indicators(df)
    latest = df.iloc[-1]
    price = latest["Close"]

    # Target/Stop-loss check
    if symbol in entry_prices:
        entry = entry_prices[symbol]
        if price >= entry * (1 + TARGET_PERCENT):
            send_telegram_alert(f"🎯 Target Hit for {symbol}!\nEntry: {entry:.2f} → Now: {price:.2f}")
            del entry_prices[symbol]
            return None
        elif price <= entry * (1 - STOPLOSS_PERCENT):
            send_telegram_alert(f"🛑 Stop-loss Hit for {symbol}!\nEntry: {entry:.2f} → Now: {price:.2f}")
            del entry_prices[symbol]
            return None

    if latest["EMA20"] > latest["EMA50"] and latest["RSI"] < 70:
        entry_prices[symbol] = price  # record entry
        return f"🔔 Buy Signal: {symbol}\nPrice: {price:.2f}\nRSI: {latest['RSI']:.2f}"
    elif latest["EMA20"] < latest["EMA50"] and latest["RSI"] > 30:
        return f"⚠️ Sell Signal: {symbol}\nPrice: {price:.2f}\nRSI: {latest['RSI']:.2f}"
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
    time.sleep(180)  # every 3 mins
