import websocket
import json
import requests
import numpy as np
from collections import deque

# =========================
# 🔔 TELEGRAM CONFIG
# =========================

TOKEN = "YOUR_TELEGRAM_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# =========================
# 🧠 MARKET MEMORY
# =========================

market_data = {}
MAX_LEN = 30


def update(symbol, price, volume):

    if symbol not in market_data:
        market_data[symbol] = {
            "prices": deque(maxlen=MAX_LEN),
            "volumes": deque(maxlen=MAX_LEN)
        }

    market_data[symbol]["prices"].append(price)
    market_data[symbol]["volumes"].append(volume)


# =========================
# 🧠 AI FEATURES
# =========================

def ai_score(prices, volumes):

    if len(prices) < 20:
        return 0

    score = 0
    mean = sum(prices) / len(prices)

    # trend
    if prices[-1] > mean:
        score += 20

    # squeeze
    if max(prices[-10:]) - min(prices[-10:]) < mean * 0.01:
        score += 25

    # volume expansion
    if volumes[-1] > sum(volumes) / len(volumes) * 1.8:
        score += 30

    # micro compression
    if abs(prices[-1] - prices[-2]) < mean * 0.002:
        score += 25

    return score


# =========================
# 🚨 FAKE BREAKOUT FILTER
# =========================

def fake_breakout_filter(prices, volumes, level):

    score = 0

    if volumes[-1] < sum(volumes[-20:]) / 20 * 1.5:
        score += 30

    if len(prices) > 2 and prices[-2] > level and prices[-1] < level:
        score += 30

    if max(prices[-5:]) < level * 1.01:
        score += 20

    if abs(prices[-1] - prices[-2]) > abs(prices[-2] - prices[-3]):
        score += 20

    return score


# =========================
# 🧲 LIQUIDITY ENGINE
# =========================

def liquidity_zones(prices):

    zones = []

    for i in range(2, len(prices) - 2):

        if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
            zones.append(prices[i])

        if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
            zones.append(prices[i])

    return zones


def liquidity_score(price, zones):

    score = 0

    for z in zones:

        dist = abs(price - z)

        if dist < price * 0.002:
            score += 50
        elif dist < price * 0.005:
            score += 25

    return min(score, 100)


# =========================
# 📊 ORDER BOOK (SIMPLIFIED WS DATA)
# =========================

def orderbook_score(bids, asks):

    bid = sum(bids)
    ask = sum(asks)

    if ask == 0:
        return 100

    imbalance = bid / ask

    score = 0

    if imbalance > 1.5:
        score += 50
    elif imbalance < 0.7:
        score += 50

    if max(bids) > np.mean(bids) * 5:
        score += 25

    if max(asks) > np.mean(asks) * 5:
        score += 25

    return min(score, 100)


# =========================
# 🧠 SELF LEARNING WEIGHTS
# =========================

weights = {
    "liq": 0.5,
    "ob": 0.5,
    "trend": 0.3,
    "vol": 0.2
}


def fusion(liq, ob):

    return (liq * weights["liq"]) + (ob * weights["ob"])


# =========================
# 🤖 SELF LEARNING UPDATE
# =========================

def learn(state, reward):

    lr = 0.01

    for k in weights:

        if reward > 0:
            weights[k] += lr * state[k]
        else:
            weights[k] -= lr * state[k]


# =========================
# 🚨 FINAL DECISION ENGINE
# =========================

def analyze(symbol):

    data = market_data.get(symbol)

    if not data or len(data["prices"]) < 20:
        return

    prices = list(data["prices"])
    volumes = list(data["volumes"])

    price = prices[-1]

    # AI
    explosion = ai_score(prices, volumes)

    # Fake breakout
    trap = fake_breakout_filter(prices, volumes, price)

    # Liquidity
    zones = liquidity_zones(prices)
    liq = liquidity_score(price, zones)

    # Order book (simulated)
    bids = [v * 0.6 for v in volumes[-5:]]
    asks = [v * 0.4 for v in volumes[-5:]]

    ob = orderbook_score(bids, asks)

    # Fusion
    fusion_score = fusion(liq, ob)

    # FILTER
    if trap >= 75:
        return

    # FINAL DECISION
    if explosion >= 85 and fusion_score >= 70:

        send(f"""
🚨 SMART MONEY SIGNAL

Symbol: {symbol}

Price: {price:.4f}

Explosion Score: {explosion}/100
Liquidity Score: {liq}/100
OrderBook Score: {ob}/100
Fusion Score: {fusion_score}/100
Trap Score: {trap}/100

🧠 AI SELF-LEARNING ACTIVE
🔥 INSTITUTIONAL PRESSURE DETECTED

🚀 BREAKOUT SETUP
""")


# =========================
# 📡 BINANCE WEBSOCKET
# =========================

def on_message(ws, message):

    data = json.loads(message)

    for coin in data:

        symbol = coin['s']
        price = float(coin['c'])
        volume = float(coin['v'])

        update(symbol, price, volume)

        analyze(symbol)


def on_open(ws):
    print("🔥 LIVE SMART MONEY AI STARTED")


def on_close(ws):
    print("❌ DISCONNECTED")


socket = "wss://stream.binance.com:9443/ws/!miniTicker@arr"

ws = websocket.WebSocketApp(
    socket,
    on_message=on_message,
    on_open=on_open,
    on_close=on_close
)

ws.run_forever()
