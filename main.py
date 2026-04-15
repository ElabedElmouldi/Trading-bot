import time
import requests
import ccxt
import pandas as pd
import sqlite3
import math

# =========================
# ⚙️ CONFIG
# =========================
TOKEN = "8439548325:AAHOBBHy7EwcX3J5neIaf6iJuSjyGJCuZ68"
CHAT_ID = "5067771509"

START_BALANCE = 1000
RISK_PER_TRADE = 0.02  # 2%
TRADE_SIZE = 100


# =========================
# 📲 TELEGRAM
# =========================
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass


# =========================
# ⚙️ EXCHANGE
# =========================
exchange = ccxt.kucoin({"enableRateLimit": True})
markets = exchange.load_markets()
symbols = list(markets.keys())[:1000]


# =========================
# 💾 DATABASE
# =========================
conn = sqlite3.connect("trades.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS trades (
id INTEGER PRIMARY KEY AUTOINCREMENT,
symbol TEXT,
entry REAL,
exit REAL,
status TEXT,
score REAL,
time TEXT
)
""")
conn.commit()


# =========================
# 💼 PORTFOLIO
# =========================
portfolio = {
    "balance": START_BALANCE,
    "positions": {}
}


# =========================
# 📊 DATA
# =========================
def get(symbol, tf="15m"):
    try:
        return pd.DataFrame(
            exchange.fetch_ohlcv(symbol, tf, limit=120),
            columns=["t","o","h","l","c","v"]
        )
    except:
        return None


# =========================
# 🧠 ML FEATURE ENGINE
# =========================
def ml_score(df):

    if df is None:
        return 0, []

    reasons = []
    score = 0

    c = df["c"]
    v = df["v"]

    # trend
    if c.iloc[-1] > c.rolling(50).mean().iloc[-1]:
        score += 25
        reasons.append("Trend bullish")

    # momentum
    if c.iloc[-1] > c.iloc[-5]:
        score += 20
        reasons.append("Momentum up")

    # volume spike
    if v.iloc[-1] > v.mean() * 2:
        score += 20
        reasons.append("Volume spike")

    # breakout
    if c.iloc[-1] > c.rolling(20).max().iloc[-2]:
        score += 20
        reasons.append("Breakout confirmed")

    # volatility compression (squeeze)
    if c.rolling(20).std().iloc[-1] < c.mean() * 0.02:
        score += 15
        reasons.append("Squeeze detected")

    return score, reasons


# =========================
# 🧠 MULTI TIMEFRAME CONFIRMATION
# =========================
def confirm(symbol):

    for tf in ["15m", "1h", "4h"]:
        df = get(symbol, tf)

        if df is None:
            return False

        if df["c"].iloc[-1] <= df["c"].rolling(50).mean().iloc[-1]:
            return False

    return True


# =========================
# 💣 RISK ENGINE
# =========================
def calc_position_size(price):

    risk_amount = portfolio["balance"] * RISK_PER_TRADE
    size = risk_amount / (price * 0.02)

    return max(size, 1)


# =========================
# 💾 SAVE TRADE
# =========================
def save(symbol, entry, status, score, exit_price=None):

    c.execute("""
    INSERT INTO trades VALUES (NULL,?,?,?,?,?,datetime('now'))
    """, (symbol, entry, exit_price, status, score))

    conn.commit()


# =========================
# 📥 AUTO ENTRY
# =========================
def open_trade(symbol, price, score, reasons):

    if symbol in portfolio["positions"]:
        return

    size = calc_position_size(price)

    portfolio["positions"][symbol] = {
        "entry": price,
        "sl": price * 0.98,
        "size": size,
        "score": score
    }

    save(symbol, price, "OPEN", score)

    send(f"""
📥 AUTO ENTRY

{symbol}
Price: {price}
Score: {score}/100
Size: {size}

📌 Reasons:
""" + "\n".join(reasons))


# =========================
# 📤 EXIT
# =========================
def close_trade(symbol, price, reason):

    t = portfolio["positions"].pop(symbol)

    pnl = (price - t["entry"]) * t["size"]

    portfolio["balance"] += pnl

    save(symbol, t["entry"], "CLOSED", t["score"], price)

    send(f"""
📤 EXIT

{symbol}
Exit: {price}
PnL: {round(pnl,2)}$
Reason: {reason}
""")


# =========================
# 🔄 MANAGE POSITION
# =========================
def manage(symbol, price):

    t = portfolio["positions"][symbol]

    if price <= t["sl"]:
        close_trade(symbol, price, "STOP LOSS")


# =========================
# 🔍 SCANNER
# =========================
BATCH = 200
index = 0

def batch():

    global index

    start = index * BATCH
    end = start + BATCH

    data = symbols[start:end]

    index += 1
    if end >= len(symbols):
        index = 0

    return data


def scan():

    results = []

    for s in batch():

        df = get(s)

        score, reasons = ml_score(df)

        if score >= 90 and confirm(s):

            results.append({
                "symbol": s,
                "score": score,
                "price": df["c"].iloc[-1],
                "reasons": reasons
            })

        time.sleep(0.2)

    return sorted(results, key=lambda x: x["score"], reverse=True)


# =========================
# 📊 TOP SIGNALS
# =========================
def send_top(signals):

    top = signals[:3]

    if not top:
        return

    msg = "💣 INSTITUTIONAL SIGNALS\n\n"

    for s in top:
        msg += f"""
🚀 {s['symbol']}
💥 Score: {s['score']}
💰 Price: {s['price']}

📌 Reasons:
""" + "\n".join(s["reasons"]) + "\n-----------------\n"

    send(msg)


# =========================
# 🚀 START
# =========================
print("HEDGE FUND V8 STARTED")
send("🚀 V8 INSTITUTIONAL AI STARTED")

last = time.time()

while True:

    try:

        signals = scan()

        send_top(signals)

        # AUTO EXECUTION
        for s in signals[:3]:

            if s["symbol"] not in portfolio["positions"]:
                open_trade(s["symbol"], s["price"], s["score"], s["reasons"])

        # manage trades
        for sym in list(portfolio["positions"].keys()):
            try:
                price = get(sym)["c"].iloc[-1]
                manage(sym, price)
            except:
                pass

        if time.time() - last > 3600:
            send(f"📊 REPORT\nBalance: {portfolio['balance']}\nOpen: {len(portfolio['positions'])}")
            last = time.time()

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)

    time.sleep(10)
