import requests
import time

# =========================
# 🔑 إعدادات البوت
# =========================

TOKEN = "8439548325:AAHOBBHy7EwcX3J5neIaf6iJuSjyGJCuZ68"

# 👤 حسابك الشخصي
USER_CHAT_ID = "5067771509"

# 👥 المجموعة الخاصة (غيرها بالـ chat_id الحقيقي)
GROUP_CHAT_ID = "-1003692815602"

# =========================
# 📡 إرسال رسالة تيليغرام
# =========================

def send_message(text, send_to_group=True):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    chat_ids = [USER_CHAT_ID]

    if send_to_group:
        chat_ids.append(GROUP_CHAT_ID)

    for chat_id in chat_ids:
        try:
            requests.post(url, data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            })
        except Exception as e:
            print(f"Error sending message to {chat_id}: {e}")


# =========================
# 📊 مثال إشارات تداول
# =========================

def generate_signal():
    # هذا مثال فقط (بدّلها باستراتيجيتك)
    return {
        "symbol": "BTCUSDT",
        "action": "BUY",
        "entry": 65000,
        "tp": 67000,
        "sl": 64000
    }


def format_signal(signal):
    return f"""
🚀 SIGNAL ALERT

📊 Pair: {signal['symbol']}
📈 Action: {signal['action']}

🎯 Entry: {signal['entry']}
💰 TP: {signal['tp']}
🛑 SL: {signal['sl']}
"""


# =========================
# 🔁 تشغيل البوت
# =========================

def main():
    send_message("🤖 Bot started successfully", send_to_group=False)

    while True:
        signal = generate_signal()

        message = format_signal(signal)

        # إرسال لك + للمجموعة
        send_message(message, send_to_group=True)

        print("Signal sent!")

        # كل 60 ثانية (عدّل حسب الاستراتيجية)
        time.sleep(60)


if __name__ == "__main__":
    main()
