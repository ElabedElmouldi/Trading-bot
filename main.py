import time
import os
import requests
import ccxt
import pandas as pd

# =========================
# 📲 TELEGRAM CONFIG
# =========================
TOKEN = os.getenv("8439548325:AAHOBBHy7EwcX3J5neIaf6iJuSjyGJCuZ68")
CHAT_ID = os.getenv("CHAT_ID")

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
# ⚙️ BYBIT EXCHANGE
# =========================
exchange = ccxt.bybit({
    "enableRateLimit": True,
    "options": {
        "defaultType": "spot"
    }
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
    ma_fast = df["c"].rolling(10).mean().iloc[-1]
    ma_slow = df["c"].rolling(50).mean().iloc[-1]

    if ma_fast > ma_slow:
        return "BULL"
    elif ma_fast < ma_slow:
        return "BEAR"
    return "SIDEWAYS"


# =========================
# 🧠 SCORING ENGINE
# =========================
def smart_score(df):

    c = df["c"]
    v = df["v"]

    score = 0

    # 📈 trend
    if c.iloc[-1] > c.mean():
        score += 20

    # 🚀 momentum
    if c.iloc[-1] > c.iloc[-5]:
        score += 20

    # 💥 volume spike
    if v.iloc[-1] > v.mean() * 1.5:
        score += 25

    # 📊 volatility filter
    if 0.005 < c.pct_change().std() < 0.03:
        score += 15

    # 🔥 breakout
    if c.iloc[-1] > c.rolling(20).max().iloc[-2]:
        score += 20

    return score


# =========================
# 💼 PORTFOLIO
# =========================
portfolio = {
    "balance": 1000,
    "positions": {}
}

positions = {}


# =========================
# 💰 EXECUTION ENGINE (PAPER)
# =========================
def execute(symbol,
