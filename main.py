import os
import base64
import threading
import requests
import pandas as pd

from http.server import BaseHTTPRequestHandler, HTTPServer
from openai import OpenAI

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TIMEFRAME = "15min"
MIN_CONFIDENCE = 75
MIN_PIPS = 50

VISION_MODEL = "qwen/qwen3.6-27b"

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing")

groq = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# =========================================================
# RENDER HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain"
        )
        self.end_headers()
        self.wfile.write(
            b"CryptoFlowBot is running."
        )

    def log_message(self, format, *args):
        pass


def start_server():

    port = int(
        os.getenv("PORT", "10000")
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(
        f"Health server running on {port}"
    )

    server.serve_forever()


# =========================================================
# SYMBOL
# =========================================================

def clean_symbol(symbol):

    return (
        symbol.upper()
        .strip()
        .replace("/", "")
        .replace("-", "")
        .replace("_", "")
    )


def twelve_symbol(symbol):

    symbol = clean_symbol(symbol)

    symbols = {
        "EURUSD": "EUR/USD",
        "GBPUSD": "GBP/USD",
        "USDJPY": "USD/JPY",
        "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD",
        "USDCHF": "USD/CHF",
        "NZDUSD": "NZD/USD",
        "XAUUSD": "XAU/USD",
        "GOLD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "SILVER": "XAG/USD",
    }

    return symbols.get(
        symbol,
        symbol
    )


# =========================================================
# BINANCE
# =========================================================

def get_binance_data(symbol):

    url = (
        "https://api.binance.com/"
        "api/v3/klines"
    )

    params = {
        "symbol": clean_symbol(symbol),
        "interval": "15m",
        "limit": 200
    }

    r = requests.get(
        url,
        params=params,
        timeout=15
    )

    if r.status_code != 200:
        raise RuntimeError(
            "Not a Binance symbol"
        )

    data = r.json()

    if not isinstance(data, list):
        raise RuntimeError(
            "Invalid Binance data"
        )

    df = pd.DataFrame(
        data,
        columns=[
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
        ]
    )

    for c in [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]:
        df[c] = df[c].astype(float)

    return df


# =========================================================
# TWELVE DATA
# =========================================================

def get_twelve_data(symbol):

    if not TWELVE_DATA_KEY:
        raise RuntimeError(
            "TWELVE_DATA_KEY is missing"
        )

    url = (
        "https://api.twelvedata.com/"
        "time_series"
    )

    params = {
        "symbol": twelve_symbol(symbol),
        "interval": TIMEFRAME,
        "outputsize": 200,
        "apikey": TWELVE_DATA_KEY
    }

    r = requests.get(
        url,
        params=params,
        timeout=15
    )

    data = r.json()

    if "values" not in data:
        raise RuntimeError(
            str(data)
        )

    df = pd.DataFrame(
        data["values"]
    )

    df = df.iloc[::-1].reset_index(
        drop=True
    )

    for c in [
        "open",
        "high",
        "low",
        "close"
    ]:
        df[c] = df[c].astype(float)

    return df


# =========================================================
# GET DATA
# =========================================================

def get_market_data(symbol):

    symbol = clean_symbol(symbol)

    # Crypto
    if (
        symbol.endswith("USDT")
        or symbol.endswith("USDC")
    ):
        try:
            return get_binance_data(symbol)
        except Exception:
            pass

    # Forex / Gold / Silver
    return get_twelve_data(symbol)


# =========================================================
# INDICATORS
# =========================================================

def indicators(df):

    df = df.copy()

    df["EMA20"] = (
        df["close"]
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
    )

    df["EMA50"] = (
        df["close"]
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
    )

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        pd.NA
    )

    df["RSI"] = (
        100 -
        (100 / (1 + rs))
    )

    high_low = (
        df["high"] -
        df["low"]
    )

    high_close = (
        df["high"] -
        df["close"].shift()
    ).abs()

    low_close = (
        df["low"] -
        df["close"].shift()
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


# =========================================================
# PIP SIZE
# =========================================================

def pip_size(symbol):

    symbol = clean_symbol(symbol)

    if "JPY" in symbol:
        return 0.01

    if symbol in [
        "XAUUSD",
        "XAGUSD"
    ]:
        return 0.01

    if len(symbol) == 6:
        return 0.0001

    return None


# =========================================================
# MARKET ANALYSIS
# =========================================================

def analyze_market(df, symbol):

    df = indicators(df)

    row = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(row["close"])
    ema20 = float(row["EMA20"])
    ema50 = float(row["EMA50"])
    rsi = float(row["RSI"])
    atr = float(row["ATR"])

    previous_price = float(
        prev["close"]
    )

    buy = 0
    sell = 0

    buy_reasons = []
    sell_reasons = []

    # Trend
    if ema20 > ema50:
        buy += 30
        buy_reasons.append(
            "EMA20 > EMA50"
        )

    elif ema20 < ema50:
        sell += 30
        sell_reasons.append(
            "EMA20 < EMA50"
        )

    # Price
    if price > ema20:
        buy += 20
        buy_reasons.append(
            "Price above EMA20"
        )

    elif price < ema20:
        sell += 20
        sell_reasons.append(
            "Price below EMA20"
        )

    # RSI
    if 52 <= rsi <= 68:
        buy += 20
        buy_reasons.append(
            "Bullish RSI"
        )

    elif 32 <= rsi <= 48:
        sell += 20
        sell_reasons.append(
            "Bearish RSI"
        )

    # Momentum
    if price > previous_price:
        buy += 15
        buy_reasons.append(
            "Positive momentum"
        )

    elif price < previous_price:
        sell += 15
        sell_reasons.append(
            "Negative momentum"
        )

    confidence = max(
        buy,
        sell
    )

    difference = abs(
        buy - sell
    )

    # =====================================================
    # UNCERTAIN
    # =====================================================

    if (
        confidence < MIN_CONFIDENCE
        or difference < 15
    ):

        return {
            "signal": "WAIT",
            "condition": "UNCERTAIN",
            "confidence": confidence,
            "price": price,
            "reason": (
                "Market direction is "
                "not sufficiently clear."
            )
        }

    # =====================================================
    # BUY
    # =====================================================

    if buy > sell:

        buy_limit = (
            price - atr * 0.40
        )

        sl = (
            buy_limit - atr * 1.5
        )

        minimum_move = (
            MIN_PIPS * pip_size(symbol)
            if pip_size(symbol)
            else atr * 1.5
        )

        tp1 = buy_limit + max(
            atr * 1.5,
            minimum_move
        )

        tp2 = buy_limit + max(
            atr * 2.5,
            minimum_move * 2
        )

        tp3 = buy_limit + max(
            atr * 3.5,
            minimum_move * 3
        )

        return {
            "signal": "BUY",
            "condition": "GOOD",
            "confidence": confidence,
            "price": price,
            "limit": buy_limit,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "reasons": buy_reasons
        }

    # =====================================================
    # SELL
    # =====================================================

    sell_limit = (
        price + atr * 0.40
    )

    sl = (
        sell_limit + atr * 1.5
    )

    minimum_move = (
        MIN_PIPS * pip_size(symbol)
        if pip_size(symbol)
        else atr * 1.5
    )

    tp1 = sell_limit - max(
        atr * 1.5,
        minimum_move
    )

    tp2 = sell_limit - max(
        atr * 2.5,
        minimum_move * 2
    )

    tp3 = sell_limit - max(
        atr * 3.5,
        minimum_move * 3
    )

    return {
        "signal": "SELL",
        "condition": "GOOD",
        "confidence": confidence,
        "price": price,
        "limit": sell_limit,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "reasons": sell_reasons
    }


# =========================================================
# FORMAT PRICE
# =========================================================

def fmt(value, symbol):

    symbol = clean_symbol(symbol)

    if "JPY" in symbol:
        return f"{value:.3f}"

    if symbol in [
        "XAUUSD",
        "XAGUSD"
    ]:
        return f"{value:.2f}"

    if len(symbol) == 6:
        return f"{value:.5f}"

    return f"{value:.2f}"


# =========================================================
# MESSAGE
# =========================================================

def format_result(symbol, result):

    confidence = result[
        "confidence"
    ]

    # Uncertain
    if result["condition"] == "UNCERTAIN":

        return (
            "⚠️ CRYPTOFLOWBOT\n\n"
            f"Symbol: {symbol}\n\n"
            "⚠️ MARKET: UNCERTAIN\n"
            f"Confidence: {confidence}%\n\n"
            "Market direction is not clear.\n"
            "🚫 DO NOT TRADE\n"
            "⏳ WAIT FOR CONFIRMATION."
        )

    reasons = "\n".join(
        "• " + r
        for r in result["reasons"]
    )

    if result["signal"] == "BUY":

        return (
            "🟢 CRYPTOFLOWBOT\n\n"
            f"Symbol: {symbol}\n"
            "MARKET: GOOD\n\n"
            "📈 TRADE OPPORTUNITY: BUY\n"
            f"Confidence: {confidence}%\n\n"
            "📍 TRADE SETUP\n"
            f"🟢 BUY LIMIT: "
            f"{fmt(result['limit'], symbol)}\n"
            f"🛑 SL: "
            f"{fmt(result['sl'], symbol)}\n\n"
            f"🎯 TP1: "
            f"{fmt(result['tp1'], symbol)}\n"
            f"🎯 TP2: "
            f"{fmt(result['tp2'], symbol)}\n"
            f"🎯 TP3: "
            f"{fmt(result['tp3'], symbol)}\n\n"
            "🧠 REASONS\n"
            f"{reasons}\n\n"
            "⚠️ Confidence is a strategy score, "
            "not a guaranteed win rate."
        )

    return (
        "🔴 CRYPTOFLOWBOT\n\n"
        f"Symbol: {symbol}\n"
        "MARKET: GOOD\n\n"
        "📉 TRADE OPPORTUNITY: SELL\n"
        f"Confidence: {confidence}%\n\n"
        "📍 TRADE SETUP\n"
        f"🔴 SELL LIMIT: "
        f"{fmt(result['limit'], symbol)}\n"
        f"🛑 SL: "
        f"{fmt(result['sl'], symbol)}\n\n"
        f"🎯 TP1: "
        f"{fmt(result['tp1'], symbol)}\n"
        f"🎯 TP2: "
        f"{fmt(result['tp2'], symbol)}\n"
        f"🎯 TP3: "
        f"{fmt(result['tp3'], symbol)}\n\n"
        "🧠 REASONS\n"
        f"{reasons}\n\n"
        "⚠️ Confidence is a strategy score, "
        "not a guaranteed win rate."
    )


# =========================================================
# TEXT HANDLER
# =========================================================

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    symbol = clean_symbol(
        update.message.text
    )

    if len(symbol) < 4:
        await update.message.reply_text(
            "⚠️ Send a symbol.\n\n"
            "Example:\n"
            "BTCUSDT\n"
            "EURUSD\n"
            "XAUUSD"
        )
        return

    await update.message.reply_text(
        f"🔎 Analyzing {symbol}..."
    )

    try:

        df = get_market_data(symbol)

        result = analyze_market(
            df,
            symbol
        )

        await update.message.reply_text(
            format_result(
                symbol,
                result
            )
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Could not analyze "
            f"{symbol}.\n\n{e}"
        )


# =========================================================
# CHART ANALYSIS WITH GROQ
# =========================================================

def analyze_chart(image_bytes, symbol):

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    response = groq.chat.completions.create(

        model=VISION_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a technical analysis "
                    "assistant. Analyze trading charts "
                    "carefully. Never guarantee profit."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Analyze this {symbol} chart.\n\n"
                            "Give:\n"
                            "1. Trend\n"
                            "2. Market structure\n"
                            "3. Momentum\n"
                            "4. Support/resistance\n"
                            "5. GOOD, BAD or UNCERTAIN\n"
                            "6. Whether a trade should be "
                            "considered or avoided.\n\n"
                            "Do not invent prices."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":
                            "data:image/jpeg;base64,"
                            + encoded
                        }
                    }
                ]
            }
        ],

        temperature=0.1
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


# =========================================================
# PHOTO HANDLER
# =========================================================

async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    caption = (
        update.message.caption
        or ""
    ).strip()

    if not caption:

        await update.message.reply_text(
            "📷 Chart received.\n\n"
            "Please put the symbol in the "
            "caption.\n\n"
            "Example: XAUUSD"
        )

        return

    symbol = clean_symbol(
        caption
    )

    await update.message.reply_text(
        f"📷 Analyzing {symbol} chart..."
    )

    try:

        photo = update.message.photo[-1]

        file = await context.bot.get_file(
            photo.file_id
        )

        image = (
            await file.download_as_bytearray()
        )

        # Live market analysis
        df = get_market_data(symbol)

        result = analyze_market(
            df,
            symbol
        )

        # Groq vision analysis
        chart = analyze_chart(
            bytes(image),
            symbol
        )

        message = format_result(
            symbol,
            result
        )

        message += (
            "\n\n📷 CHART ANALYSIS\n\n"
            + chart
        )

        await update.message.reply_text(
            message
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Chart analysis failed.\n\n{e}"
        )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 CRYPTOFLOWBOT\n\n"
        "Send ONE symbol.\n\n"
        "Examples:\n"
        "BTCUSDT\n"
        "ETHUSDT\n"
        "EURUSD\n"
        "XAUUSD\n\n"
        "📷 You can also send a chart "
        "with the symbol in the caption.\n\n"
        "🟢 GOOD = trade opportunity\n"
        "⚠️ UNCERTAIN = wait\n"
        "🔴 BAD = avoid"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    threading.Thread(
        target=start_server,
        daemon=True
    ).start()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            handle_text
        )
    )

    print(
        "CRYPTOFLOWBOT is running..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
