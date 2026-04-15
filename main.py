import time
import requests
import ccxt
import pandas as pd

# =========================
# 📲 TELEGRAM
# =========================
TOKEN = "8439548325:AAHOBBHy7EwcX3J5neIaf6iJuSjyGJCuZ68"
CHAT_ID = "5067771509"

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
# ⚙️ KUCOIN EXCHANGE
# =========================
exchange = ccxt.kucoin({
    "enableRateLimit": True
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
    slow = df["c"].rolling(50).mean().iloc[-1]

    if fast > slow:
        return "BULL"
    elif fast < slow:
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
# 💰 EXECUTION (PAPER)
# =========================
def execute(symbol, price, score):

    if symbol not in positions:

        size = portfolio["balance"] * (score / 1000)

        positions[symbol] = {
            "entry": price,
            "tp": price * 1.05,
            "sl": price * 0.98,
            "size": size
        }

        return "OPEN"

    pos = positions[symbol]

    if price >= pos["tp"]:
        portfolio["balance"] += pos["size"] * 0.05
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
def scan_market():

    send_message("🔍 Scanning KuCoin market...")

    results = []

    for s in symbols:

        try:
            df = get_data(s)

            regime = get_regime(df)
            score = smart_score(df)
            price = df["c"].iloc[-1]

            if regime == "BULL" and score >= 90:

                results.append({
                    "symbol": s,
                    "score": score,
                    "price": price,
                    "regime": regime
                })

        except Exception as e:
            print("Error:", e)

    return sorted(results, key=lambda x: x["score"], reverse=True)


# =========================
# 📲 TELEGRAM REPORTS
# =========================
def send_opportunities(signals):

    if not signals:
        return

    msg = "🔥 KUCOIN TOP OPPORTUNITIES\n\n"

    for s in signals[:5]:

        msg += (
            f"🪙 {s['symbol']}\n"
            f"📊 Score: {s['score']}\n"
            f"💰 Price: {s['price']}\n"
            f"-------------------\n"
        )

    send_message(msg)


def send_trade(symbol, result, score):

    send_message(
        f"📊 TRADE UPDATE\n"
        f"{symbol}\n"
        f"Result: {result}\n"
        f"Score: {score}"
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
print("🤖 KUCOIN BOT STARTED")

send_message("🚀 Bot Started on KuCoin")

cycle = 0

while True:

    cycle += 1

    signals = scan_market()

    send_opportunities(signals)

    if signals:

        best = signals[0]

        result = execute(best["symbol"], best["price"], best["score"])

        if result:
            send_trade(best["symbol"], result, best["score"])

    send_portfolio(cycle)

    time.sleep(20)
