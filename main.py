# cryptoflowbot.py
# Python 3.10+
#
# Install:
# pip install python-telegram-bot requests pandas
#
# Set these environment variables:
# TELEGRAM_BOT_TOKEN
# TELEGRAM_CHAT_ID
# TWELVE_DATA_KEY
#
# IMPORTANT:
# Never publish your real tokens/API keys.

import os
import time
import requests
import pandas as pd

from telegram import Bot

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_KEY")



TIMEFRAME = "15min"
CHECK_SECONDS = 60

MIN_CONFIDENCE = 75

# Crypto symbols supported by Binance
CRYPTO_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
]

# Forex / metals / commodities
TWELVE_SYMBOLS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "USD/CHF",
    "NZD/USD",
    "XAU/USD",
    "XAG/USD",
]

# Remember last alert
last_alert = {}


# ============================================================
# TELEGRAM
# ============================================================

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError(
        "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first."
    )

bot = Bot(token=BOT_TOKEN)


async def send_telegram(message: str):
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )
        print("Telegram sent.")
    except Exception as e:
        print(f"Telegram error: {e}")
    
        
            
            
            
        
        
    
        


# ============================================================
# BINANCE DATA
# ============================================================

def get_binance_data(symbol, limit=100):

    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": "15m",
        "limit": limit
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()

    df = pd.DataFrame(data, columns=[
        "time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "qav",
        "trades",
        "tbav",
        "tqav",
        "ignore"
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    return df


# ============================================================
# TWELVE DATA
# ============================================================

def get_twelve_data(symbol, limit=100):

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "outputsize": limit,
        "apikey": TWELVE_DATA_KEY
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()

    if "values" not in data:
        raise RuntimeError(str(data))

    df = pd.DataFrame(data["values"])

    df = df.iloc[::-1].reset_index(drop=True)

    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)

    return df


# ============================================================
# INDICATORS
# ============================================================

def calculate_indicators(df):

    df["EMA20"] = df["close"].ewm(
        span=20,
        adjust=False
    ).mean()

    df["EMA50"] = df["close"].ewm(
        span=50,
        adjust=False
    ).mean()

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)

    df["RSI"] = 100 - (100 / (1 + rs))

    high_low = df["high"] - df["low"]

    high_close = (
        df["high"] - df["close"].shift()
    ).abs()

    low_close = (
        df["low"] - df["close"].shift()
    ).abs()

    tr = pd.concat(
        [
            high_low,
            high_close,
            low_close
        ],
        axis=1
    ).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()

    return df


# ============================================================
# MARKET ANALYSIS
# ============================================================

def analyze_market(df):

    df = calculate_indicators(df)

    row = df.iloc[-1]

    price = float(row["close"])
    ema20 = float(row["EMA20"])
    ema50 = float(row["EMA50"])
    rsi = float(row["RSI"])
    atr = float(row["ATR"])

    buy_score = 0
    sell_score = 0

    # Trend
    if ema20 > ema50:
        buy_score += 30

    if ema20 < ema50:
        sell_score += 30

    # Price location
    if price > ema20:
        buy_score += 20

    if price < ema20:
        sell_score += 20

    # RSI
    if 55 <= rsi <= 70:
        buy_score += 25

    if 30 <= rsi <= 45:
        sell_score += 25

    # Momentum
    if price > df["close"].iloc[-2]:
        buy_score += 15

    if price < df["close"].iloc[-2]:
        sell_score += 15

    confidence = max(
        buy_score,
        sell_score
    )

    # --------------------------------------------------------
    # NO TRADE
    # --------------------------------------------------------

    if confidence < MIN_CONFIDENCE:

        return {
            "signal": "NO TRADE",
            "confidence": confidence,
            "price": price,
            "atr": atr
        }

    # --------------------------------------------------------
    # BUY
    # --------------------------------------------------------

    if buy_score > sell_score:

        entry = price

        sl = entry - (atr * 1.5)

        tp1 = entry + (atr * 1.0)
        tp2 = entry + (atr * 2.0)
        tp3 = entry + (atr * 3.0)

        ml = (tp1 + tp2) / 2

        return {
            "signal": "BUY",
            "confidence": confidence,
            "price": price,
            "entry": entry,
            "ml": ml,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "sl": sl,
            "atr": atr
        }

    # --------------------------------------------------------
    # SELL
    # --------------------------------------------------------

    entry = price

    sl = entry + (atr * 1.5)

    tp1 = entry - (atr * 1.0)
    tp2 = entry - (atr * 2.0)
    tp3 = entry - (atr * 3.0)

    ml = (tp1 + tp2) / 2

    return {
        "signal": "SELL",
        "confidence": confidence,
        "price": price,
        "entry": entry,
        "ml": ml,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "sl": sl,
        "atr": atr
    }


# ============================================================
# FORMAT MESSAGE
# ============================================================

def format_signal(symbol, result):

    signal = result["signal"]
    confidence = result["confidence"]

    if signal == "NO TRADE":

        return (
            "⚠️ CRYPTOFLOWBOT\n\n"
            f"Symbol: {symbol}\n"
            "🚫 NO TRADE\n\n"
            "Market condition is unclear.\n"
            f"Confidence: {confidence}%\n\n"
            "⛔ Wait for confirmation."
        )

    emoji = "🟢" if signal == "BUY" else "🔴"

    return (
        "🚨 CRYPTOFLOWBOT ALERT\n\n"
        f"Symbol: {symbol}\n"
        f"{emoji} SIGNAL: {signal}\n"
        f"📊 Confidence: {confidence}%\n\n"
        "📍 TRADING ZONE\n"
        f"{'BUY ZONE' if signal == 'BUY' else 'SELL ZONE'}\n\n"
        f"Entry / SP: {result['entry']:.5f}\n"
        f"ML: {result['ml']:.5f}\n\n"
        f"🎯 TP1: {result['tp1']:.5f}\n"
        f"🎯 TP2: {result['tp2']:.5f}\n"
        f"🎯 TP3: {result['tp3']:.5f}\n\n"
        f"🛑 SL: {result['sl']:.5f}\n\n"
        "⏱ Timeframe: M15\n"
        "⚠️ Signal is technical analysis, not a guarantee."
    )


# ============================================================
# DUPLICATE ALERT PROTECTION
# ============================================================

def should_alert(symbol, result):

    signal = result["signal"]

    key = (
        signal,
        round(result["confidence"], 0)
    )

    if last_alert.get(symbol) == key:
        return False

    last_alert[symbol] = key

    return True


# ============================================================
# SCAN SYMBOL
# ============================================================

def scan_symbol(symbol, source):

    try:

        if source == "BINANCE":
            df = get_binance_data(symbol)

        else:
            df = get_twelve_data(symbol)

        result = analyze_market(df)

        if should_alert(symbol, result):

            message = format_signal(
                symbol,
                result
            )

            send_telegram(message)

        print(
            symbol,
            result["signal"],
            result["confidence"]
        )

    except Exception as e:

        print(
            "ERROR",
            symbol,
            str(e)
        )


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    send_telegram(
        "🤖 CRYPTOFLOWBOT STARTED\n\n"
        "📊 Multi-Symbol Market Monitor\n"
        "⏱ Timeframe: M15\n"
        "🔔 Telegram Alerts: ON"
    )

    while True:

        # Crypto
        for symbol in CRYPTO_SYMBOLS:

            scan_symbol(
                symbol,
                "BINANCE"
            )

        # Forex / Metals
        for symbol in TWELVE_SYMBOLS:

            scan_symbol(
                symbol,
                "TWELVE"
            )

        time.sleep(CHECK_SECONDS)


if __name__ == "__main__":
    main()
