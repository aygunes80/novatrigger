import json
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yfinance as yf
import os

# Ortam değişkenlerinden ayarları al
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
CHECK_INTERVAL_MINUTES = int(os.environ.get("CHECK_INTERVAL_MINUTES", 10))

def load_watchlist():
    with open("watchlist.json", "r") as file:
        return json.load(file)

def rsi_strategy(symbol):
    try:
        data = yf.download(symbol, period="7d", interval="1h")
        if len(data) < 14:
            return False, 0
        delta = data["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        last_rsi = rsi.iloc[-1]
        return last_rsi < 30, round(last_rsi, 2)
    except:
        return False, 0

def send_email(subject, message):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

def main():
    print("NovaTrigger başlatıldı.")
    while True:
        watchlist = load_watchlist()
        for symbol in watchlist:
            signal, rsi = rsi_strategy(symbol)
            if signal:
                subject = f"📈 Alım Sinyali: {symbol}"
                message = f"{symbol} için RSI: {rsi}
Fırsat oluştu!"
                send_email(subject, message)
                print(f"Gönderildi: {subject}")
            else:
                print(f"{symbol}: RSI {rsi} → Sinyal yok.")
        time.sleep(CHECK_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()