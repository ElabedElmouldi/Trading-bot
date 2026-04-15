import time
import requests
import ccxt
import pandas as pd
import sqlite3

# =========================
# 📲 TELEGRAM
# =========================
TOKEN = "8439548325:AAHOBBHy7EwcX3J5neIaf6iJuSjyGJCuZ68"
CHAT_ID = "5067771509"

def send_message(msg):
    if not TOKEN or not CHAT_ID:
        print(msg)
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
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
    "balance": 1000,
    "positions": {}
}

TRADE_SIZE = 100


# =========================
# 📊 DATA
# =========================
def get_data(symbol, tf="15m"):
    try:
        return pd.DataFrame(
            exchange.fetch_ohlcv(symbol, tf, limit=120),
            columns=["t","o","h","l","c","v"]
        )
    except:
        return None


# =========================
# 💣 SCORE ENGINE
# =========================
def score_coin(df):

    if df is None:
        return 0

    score = 0

    # trend
    if df["c"].iloc[-1] > df["c"].rolling(50).mean().iloc[-1]:
        score += 30

    # volume
    if df["v"].iloc[-1] > df["v"].mean() * 2:
        score += 25

    # breakout
    if df["c"].iloc[-1] > df["c"].rolling(20).max().iloc[-2]:
        score += 25

    # squeeze
    if df["c"].rolling(20).std().iloc[-1] < df["c"].mean() * 0.02:
        score += 20

    return score


# =========================
# 💾 SAVE TRADE
# =========================
def save_trade(symbol, entry, status, score, exit_price=None):

    c.execute("""
    INSERT INTO trades (symbol, entry, exit, status, score, time)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (symbol, entry, exit_price, status, score))

    conn.commit()


# =========================
# 📥 OPEN TRADE
# =========================
def open_trade(symbol, price, score):

    if symbol in portfolio["positions"]:
        return

    portfolio["positions"][symbol] = {
        "entry": price,
        "sl": price * 0.98,
        "score": score
    }

    save_trade(symbol, price, "OPEN", score)

    send_message(
        f"""📥 ENTRY
{symbol}
Price: {price}
Score: {score}
SL: {price*0.98}"""
    )


# =========================
# 📤 CLOSE TRADE
# =========================
def close_trade(symbol, price, reason):

    t = portfolio["positions"].pop(symbol)

    pnl = (price - t["entry"]) / t["entry"] * TRADE_SIZE

    portfolio["balance"] += pnl

    save_trade(symbol, t["entry"], "CLOSED", t["score"], price)

    send_message(
        f"""📤 EXIT
{symbol}
Price: {price}
PnL: {round(pnl,2)}$
Reason: {reason}"""
    )


# =========================
# 🔄 MANAGE TRADE
# =========================
def manage(symbol, price):

    t = portfolio["positions"][symbol]

    if price <= t["sl"]:
        close_trade(symbol, price, "STOP LOSS")


# =========================
# 🔍 SCANNER (1000 coins / batch 200)
# =========================
def scan_market():

    results = []
    batch_size = 200

    for i in range(0, len(symbols), batch_size):

        batch = symbols[i:i+batch_size]

        for s in batch:

            df = get_data(s)
            sc = score_coin(df)

            if sc >= 90:

                price = df["c"].iloc[-1]

                results.append({
                    "symbol": s,
                    "score": sc,
                    "price": price
                })

        time.sleep(2)  # rest between batches

    return sorted(results, key=lambda x: x["score"], reverse=True)


# =========================
# 📊 TOP 3 ONLY
# =========================
def send_top(signals):

    top = signals[:3]

    if not top:
        return

    msg = "💣 TOP EXPLOSION COINS\n\n"

    for s in top:
        msg += f"""
🚀 {s['symbol']}
💥 Score: {s['score']}
💰 Price: {s['price']}
-----------------
"""

    send_message(msg)


# =========================
# 📊 HOURLY REPORT
# =========================
def hourly_report():

    c.execute("SELECT COUNT(*) FROM trades WHERE status='OPEN'")
    open_trades = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM trades WHERE status='CLOSED'")
    closed_trades = c.fetchone()[0]

    send_message(
        f"""📊 HOURLY REPORT
💼 Balance: {portfolio['balance']}
📥 Open: {open_trades}
📤 Closed: {closed_trades}"""
    )


# =========================
# 🚀 MAIN LOOP
# =========================
print("HEDGE FUND AI STARTED")

last_hour = time.time()

while True:

    signals = scan_market()

    send_top(signals)

    # open trades
    for s in signals[:3]:
        if s["symbol"] not in portfolio["positions"]:
            open_trade(s["symbol"], s["price"], s["score"])

    # manage trades
    for sym in list(portfolio["positions"].keys()):
        try:
            df = get_data(sym)
            price = df["c"].iloc[-1]
            manage(sym, price)
        except:
            pass

    # hourly report
    if time.time() - last_hour > 3600:
        hourly_report()
        last_hour = time.time()

    time.sleep(30)
