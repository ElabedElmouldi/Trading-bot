import time
import requests
import ccxt
import pandas as pd

# =========================
# 📲 TELEGRAM
# =========================
TOKEN = "8439548325:AAHOBBHy7EwcX3J5neIaf6iJuSjyGJCuZ68"
CHAT_ID = "5067771509"

def send_message(msg):
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
# 🔁 ROTATION SYSTEM (IMPORTANT)
# =========================
BATCH_SIZE = 200
cycle_index = 0


def get_batch():
    global cycle_index

    start = cycle_index * BATCH_SIZE
    end = start + BATCH_SIZE

    batch = symbols[start:end]

    cycle_index += 1

    if end >= len(symbols):
        cycle_index = 0

    return batch


# =========================
# 🧠 SAFE FETCH (NO CRASH)
# =========================
def safe_fetch(symbol):

    for i in range(3):
        try:
            return pd.DataFrame(
                exchange.fetch_ohlcv(symbol, "15m", limit=120),
                columns=["t","o","h","l","c","v"]
            )
        except:
            time.sleep(2)

    return None


# =========================
# 💣 SCORE ENGINE
# =========================
def score(df):

    if df is None:
        return 0

    s = 0

    # trend
    if df["c"].iloc[-1] > df["c"].rolling(50).mean().iloc[-1]:
        s += 30

    # volume spike
    if df["v"].iloc[-1] > df["v"].mean() * 2:
        s += 25

    # breakout
    if df["c"].iloc[-1] > df["c"].rolling(20).max().iloc[-2]:
        s += 25

    # squeeze
    if df["c"].rolling(20).std().iloc[-1] < df["c"].mean() * 0.02:
        s += 20

    return s


# =========================
# 🔍 SCAN ONE CYCLE
# =========================
def scan_cycle():

    batch = get_batch()

    results = []

    for s in batch:

        df = safe_fetch(s)

        sc = score(df)

        if sc >= 90:

            results.append({
                "symbol": s,
                "score": sc,
                "price": df["c"].iloc[-1]
            })

        time.sleep(0.3)  # 🔥 anti-ban delay

    return sorted(results, key=lambda x: x["score"], reverse=True)


# =========================
# 📊 TOP SIGNALS
# =========================
def send_top(signals):

    top = signals[:3]

    if not top:
        return

    msg = "💣 TOP OPPORTUNITIES\n\n"

    for s in top:
        msg += f"""
🚀 {s['symbol']}
💥 Score: {s['score']}
💰 Price: {s['price']}
-----------------
"""

    send_message(msg)


# =========================
# 🚀 MAIN LOOP (STABLE)
# =========================
print("STABLE AI SCANNER STARTED")

last_report = time.time()

while True:

    try:

        signals = scan_cycle()

        send_top(signals)

        # report every 5 min (not spam)
        if time.time() - last_report > 300:
            send_message(f"📊 Cycle update: {len(signals)} signals found")
            last_report = time.time()

    except Exception as e:

        print("Reconnect safe recovery:", e)
        time.sleep(5)

    time.sleep(10)
