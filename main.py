import time
import os
import requests
import ccxt
import pandas as pd
import numpy as np

# =========================
# 📲 TELEGRAM
# =========================
TOKEN = os.getenv("8439548325:AAHOBBHy7EwcX3J5neIaf6iJuSjyGJCuZ68")
CHAT_ID = os.getenv("5067771509")

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
# ⚙️ EXCHANGE
# =========================
exchange = ccxt.binance()

symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]


# =========================
# 📊 DATA
# =========================
def get_data(symbol):
    df = pd.DataFrame(
        exchange.fetch_ohlcv(symbol, "5m", limit=120),
        columns=["t","o","h","l","c","v"]
    )
    return df


# =========================
# 🧠 AGENT 1 — TREND HUNTER
# =========================
def agent_trend(df):
    ma1 = df["c"].rolling(10).mean().iloc[-1]
    ma2 = df["c"].rolling(30).mean().iloc[-1]
    return 1 if ma1 > ma2 else 0


# =========================
# 🧠 AGENT 2 — SMART MONEY
# =========================
def agent_smart_money(df):
    v = df["v"]
    c = df["c"]

    if v.iloc[-1] > v.mean() * 1.5 and c.iloc[-1] > c.iloc[-5]:
        return 1
    return 0


# =========================
# 🧠 AGENT 3 — MOMENTUM
# =========================
def agent_momentum(df):
    return 1 if df["c"].iloc[-1] > df["c"].iloc[-10] else 0


# =========================
# 🧠 AGENT 4 — RISK FILTER
# =========================
def agent_risk(df):
    vol = df["c"].pct_change().std()
    return 1 if 0.005 < vol < 0.03 else 0


# =========================
# 🧠 CONSENSUS ENGINE
# =========================
def consensus_score(df):

    votes = [
        agent_trend(df),
        agent_smart_money(df),
        agent_momentum(df),
        agent_risk(df)
    ]

    return sum(votes)  # max = 4


# =========================
# 💼 PORTFOLIO
# =========================
portfolio = {
    "balance": 1000,
    "positions": {}
}

positions = {}


# =========================
# 💰 EXECUTION ENGINE
# =========================
def execute(symbol, price, score):

    if symbol not in positions:

        size = portfolio["balance"] * (score / 10)

        positions[symbol] = {
            "entry": price,
            "tp": price * 1.04,
            "sl": price * 0.98,
            "size": size
        }

        return "OPEN"

    pos = positions[symbol]

    if price >= pos["tp"]:
        portfolio["balance"] += pos["size"] * 0.04
        del positions[symbol]
        return "TP"

    if price <= pos["sl"]:
        portfolio["balance"] -= pos["size"] * 0.02
        del positions[symbol]
        return "SL"

    return None


# =========================
# 🔍 SCANNER
# =========================
def scan():

    results = []

    for s in symbols:

        try:

            df = get_data(s)

            score = consensus_score(df)

            price = df["c"].iloc[-1]

            # 🔥 INSTITUTIONAL FILTER
            if score >= 3:

                results.append({
                    "symbol": s,
                    "score": score,
                    "price": price
                })

        except:
            continue

    return sorted(results, key=lambda x: x["score"], reverse=True)


# =========================
# 📲 REPORTS
# =========================
def send_opportunities(signals):

    if not signals:
        return

    msg = "🏦 MULTI-AGENT OPPORTUNITIES\n\n"

    for s in signals[:5]:

        msg += (
            f"🪙 {s['symbol']}\n"
            f"🤖 Score: {s['score']}/4\n"
            f"💰 Price: {s['price']}\n"
            f"------------------\n"
        )

    send_message(msg)


def send_trade(symbol, result, score):

    send_message(
        f"📊 TRADE\n"
        f"{symbol}\n"
        f"Result: {result}\n"
        f"Agents Score: {score}/4"
    )


def send_portfolio(cycle):

    send_message(
        f"💼 PORTFOLIO\n"
        f"Balance: {portfolio['balance']}\n"
        f"Positions: {len(positions)}\n"
        f"Cycle: {cycle}"
    )


# =========================
# 🚀 MAIN LOOP
# =========================
print("🤖 HEDGE FUND AI V20 MULTI-AGENT STARTED")

send_message("🚀 V20 Multi-Agent AI Started")

cycle = 0

while True:

    cycle += 1

    signals = scan()

    send_opportunities(signals)

    if signals:

        best = signals[0]

        result = execute(best["symbol"], best["price"], best["score"])

        if result:
            send_trade(best["symbol"], result, best["score"])

    send_portfolio(cycle)

    time.sleep(20)
