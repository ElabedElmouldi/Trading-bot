import time
import requests
import ccxt
import pandas as pd

# =========================
# 📲 TELEGRAM CONFIG
# ==================

TOKEN = "8439548325:AAHOBBHy7EwcX3J5neIaf6iJuSjyGJCuZ68"
CHAT_ID = "5067771509
def send_message(text):

    if not TOKEN or not CHAT_ID:
        print(text)
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except:
        pass


# =========================
# 🚀 STARTUP MESSAGE
# =========================
def startup_message():
    send_message(
        "🤖 BOT STARTED\n"
        "🚀 System is running\n"
        "🔍 Searching for opportunities..."
    )


# =========================
# ⚙️ BYBIT EXCHANGE
# =========================
exchange = ccxt.bybit({
    "enableRateLimit": True,
    "options": {"defaultType": "spot"}
})

exchange.load_markets()

symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]


# =========================
# 📊 DATA
# =========================
def get_data(symbol):

    ohlcv = exchange.fetch_ohlcv(symbol, "5m", limit=120)

    df = pd.DataFrame(ohlcv, columns=["t","o","h","l","c","v"])

    return df


# =========================
# 🌍 MARKET REGIME
# =========================
def get_regime(df):

    fast = df["c"].rolling(10).mean().iloc[-1]
    slow =
