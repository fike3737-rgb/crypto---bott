# main.py
# CryptoFlowBot
# Python 3.10+

import os
import io
import base64
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import pandas as pd

from groq import Groq

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# =========================================================
# SETTINGS
# =========================================================

TIMEFRAME = "15min"
CANDLE_LIMIT = 120

GOOD_MARKET = 70
MIN_PIPS = 100

# Groq vision model
VISION_MODEL = "qwen/qwen3.6-27b"

# Scan settings
SCAN_DELAY = 0.12
SCAN_TOP_RESULTS = 10

# 0 = scan all Binance USDT symbols
MAX_SCAN_SYMBOLS = 0


# =========================================================
# SYMBOLS
# =========================================================

FOREX_SYMBOLS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "USD/CHF",
    "NZD/USD",

    "EUR/GBP",
    "EUR/JPY",
    "GBP/JPY",
    "AUD/JPY",
    "CAD/JPY",
    "CHF/JPY",
    "NZD/JPY",

    "EUR/AUD",
    "EUR/CAD",
    "EUR/CHF",
    "GBP/AUD",
    "GBP/CAD",
    "GBP/CHF",
    "AUD/CAD",
    "AUD/CHF",
    "AUD/NZD",
    "CAD/CHF",
    "NZD/CAD",
    "NZD/CHF",
]

METAL_SYMBOLS = [
    "XAU/USD",
    "XAG/USD",
]

CRYPTO_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "BCHUSDT",
    "TRXUSDT",
    "ATOMUSDT",
    "ETCUSDT",
    "FILUSDT",
    "NEARUSDT",
    "APTUSDT",
    "ARBUSDT",
    "OPUSDT",
]

STATIC_SCAN_SYMBOLS = FOREX_SYMBOLS + METAL_SYMBOLS + CRYPTO_SYMBOLS

# Symbols shown as clickable Telegram buttons.
AVAILABLE_SYMBOLS = STATIC_SCAN_SYMBOLS


# =========================================================
# VALIDATION
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is missing."
    )

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing."
    )


groq_client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(
            b"CryptoFlowBot is running."
        )

    def log_message(self, format, *args):
        return


def start_health_server():

    port = int(os.getenv("PORT", "10000"))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"Health server running on port {port}")

    server.serve_forever()


# =========================================================
# TELEGRAM HELPERS
# =========================================================

async def send_message(
    context: ContextTypes.DEFAULT_TYPE,
    text: str
):

    if CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=text
            )
        except Exception as e:
            print("Telegram send error:", e)


# =========================================================
# SYMBOL NORMALIZATION
# =========================================================

def normalize_symbol(symbol: str) -> str:

    symbol = symbol.strip().upper()

    symbol = symbol.replace(
        " ",
        ""
    )

    symbol = symbol.replace(
        "-",
        ""
    )

    symbol = symbol.replace(
        "_",
        ""
    )

    # FX
    if len(symbol) == 6 and "/" not in symbol:
        return (
            symbol[:3]
            + "/"
            + symbol[3:]
        )

    # Gold / silver
    if symbol in ["XAUUSD", "GOLD"]:
        return "XAU/USD"

    if symbol in ["XAGUSD", "SILVER"]:
        return "XAG/USD"

    return symbol


def binance_symbol(symbol: str) -> str:

    symbol = symbol.upper().replace(
        "/",
        ""
    )

    return symbol


def is_crypto_symbol(symbol: str) -> bool:

    symbol = symbol.upper()

    if "/" in symbol:
        return False

    quote_assets = [
        "USDT",
        "USDC",
        "FDUSD",
        "BTC",
        "ETH",
        "BNB",
    ]

    return any(
        symbol.endswith(q)
        for q in quote_assets
    )


# =========================================================
# BINANCE
# =========================================================

def get_binance_data(
    symbol: str,
    limit: int = CANDLE_LIMIT
):

    symbol = binance_symbol(symbol)

    url = (
        "https://api.binance.com"
        "/api/v3/klines"
    )

    params = {
        "symbol": symbol,
        "interval": "15m",
        "limit": limit,
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError(
            f"Binance error: {data}"
        )

    if len(data) < 50:
        raise RuntimeError(
            "Not enough Binance candles."
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
            "ignore",
        ]
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]:
        df[column] = df[column].astype(float)

    return df


# =========================================================
# TWELVE DATA
# =========================================================

def get_twelve_data(
    symbol: str,
    limit: int = CANDLE_LIMIT
):

    if not TWELVE_DATA_KEY:
        raise RuntimeError(
            "TWELVE_DATA_KEY is missing."
        )

    url = (
        "https://api.twelvedata.com"
        "/time_series"
    )

    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "outputsize": limit,
        "apikey": TWELVE_DATA_KEY,
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

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

    for column in [
        "open",
        "high",
        "low",
        "close",
    ]:
        df[column] = df[column].astype(float)

    return df


# =========================================================
# GET MARKET DATA
# =========================================================

def get_market_data(symbol: str):

    symbol = normalize_symbol(symbol)

    # Crypto → Binance first
    if is_crypto_symbol(symbol):

        try:
            return get_binance_data(
                symbol
            )
        except Exception as binance_error:

            print(
                f"Binance failed for "
                f"{symbol}: {binance_error}"
            )

            # Try Twelve Data fallback
            if symbol.endswith("USDT"):

                base = symbol[:-4]

                twelve_symbol = (
                    f"{base}/USD"
                )

                return get_twelve_data(
                    twelve_symbol
                )

            raise

    # Forex / Metals → Twelve Data
    return get_twelve_data(
        symbol
    )


# =========================================================
# INDICATORS
# =========================================================

def calculate_indicators(df):

    df = df.copy()

    # EMA
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

    # RSI
    delta = df["close"].diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.rolling(
        14
    ).mean()

    avg_loss = loss.rolling(
        14
    ).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        pd.NA
    )

    df["RSI"] = (
        100
        - (
            100
            / (1 + rs)
        )
    )

    # ATR
    high_low = (
        df["high"]
        - df["low"]
    )

    high_close = (
        df["high"]
        - df["close"].shift()
    ).abs()

    low_close = (
        df["low"]
        - df["close"].shift()
    ).abs()

    true_range = pd.concat(
        [
            high_low,
            high_close,
            low_close,
        ],
        axis=1
    ).max(axis=1)

    df["ATR"] = (
        true_range
        .rolling(14)
        .mean()
    )

    # Recent high / low
    df["RECENT_HIGH"] = (
        df["high"]
        .rolling(20)
        .max()
    )

    df["RECENT_LOW"] = (
        df["low"]
        .rolling(20)
        .min()
    )

    return df


# =========================================================
# PIP SIZE
# =========================================================

def pip_size(symbol: str):

    symbol = normalize_symbol(
        symbol
    )

    if symbol.startswith("XAU"):
        return 0.01

    if symbol.startswith("XAG"):
        return 0.01

    if "JPY" in symbol:
        return 0.01

    if (
        "/" in symbol
        and len(symbol) == 7
    ):
        return 0.0001

    # Crypto has no universal broker-defined pip.
    return None


# =========================================================
# PRICE FORMAT
# =========================================================

def format_price(price):

    if price >= 1000:
        return f"{price:.2f}"

    if price >= 100:
        return f"{price:.3f}"

    if price >= 1:
        return f"{price:.5f}"

    return f"{price:.8f}"


# =========================================================
# MARKET ANALYSIS
# =========================================================

def analyze_market(
    df,
    symbol
):

    df = calculate_indicators(
        df
    )

    row = df.iloc[-1]
    previous = df.iloc[-2]

    price = float(
        row["close"]
    )

    ema20 = float(
        row["EMA20"]
    )

    ema50 = float(
        row["EMA50"]
    )

    rsi = float(
        row["RSI"]
    )

    atr = float(
        row["ATR"]
    )

    recent_high = float(
        row["RECENT_HIGH"]
    )

    recent_low = float(
        row["RECENT_LOW"]
    )

    buy_score = 0
    sell_score = 0

    reasons_buy = []
    reasons_sell = []

    # -----------------------------------------------------
    # TREND
    # -----------------------------------------------------

    if ema20 > ema50:

        buy_score += 25

        reasons_buy.append(
            "EMA20 above EMA50"
        )

    elif ema20 < ema50:

        sell_score += 25

        reasons_sell.append(
            "EMA20 below EMA50"
        )

    # -----------------------------------------------------
    # PRICE POSITION
    # -----------------------------------------------------

    if price > ema20:

        buy_score += 20

        reasons_buy.append(
            "Price above EMA20"
        )

    elif price < ema20:

        sell_score += 20

        reasons_sell.append(
            "Price below EMA20"
        )

    # -----------------------------------------------------
    # RSI
    # -----------------------------------------------------

    if 52 <= rsi <= 70:

        buy_score += 20

        reasons_buy.append(
            f"RSI bullish ({rsi:.1f})"
        )

    elif 30 <= rsi <= 48:

        sell_score += 20

        reasons_sell.append(
            f"RSI bearish ({rsi:.1f})"
        )

    # -----------------------------------------------------
    # MOMENTUM
    # -----------------------------------------------------

    if price > float(
        previous["close"]
    ):

        buy_score += 15

        reasons_buy.append(
            "Positive momentum"
        )

    elif price < float(
        previous["close"]
    ):

        sell_score += 15

        reasons_sell.append(
            "Negative momentum"
        )

    # -----------------------------------------------------
    # STRUCTURE
    # -----------------------------------------------------

    if price > recent_low:

        buy_score += 5

    if price < recent_high:

        sell_score += 5

    # -----------------------------------------------------
    # ATR QUALITY
    # -----------------------------------------------------

    if atr > 0:

        buy_score += 5
        sell_score += 5

    # -----------------------------------------------------
    # FINAL SCORE
    # -----------------------------------------------------

    confidence = int(
        max(
            buy_score,
            sell_score
        )
    )

    if buy_score > sell_score:

        direction = "BUY"

        reasons = reasons_buy

    elif sell_score > buy_score:

        direction = "SELL"

        reasons = reasons_sell

    else:

        direction = "NONE"

        reasons = []

    # -----------------------------------------------------
    # MARKET QUALITY
    # -----------------------------------------------------

    if confidence >= GOOD_MARKET:

        market = "GOOD"

    elif confidence >= 55:

        market = "UNCERTAIN"

    else:

        market = "NO TRADE"

    # -----------------------------------------------------
    # NO TRADE
    # -----------------------------------------------------

    if market == "NO TRADE":

        return {
            "symbol": symbol,
            "market": market,
            "confidence": confidence,
            "direction": "NO TRADE",
            "price": price,
            "atr": atr,
            "reasons": reasons,
        }

    # -----------------------------------------------------
    # UNCERTAIN
    # -----------------------------------------------------

    if market == "UNCERTAIN":

        return {
            "symbol": symbol,
            "market": market,
            "confidence": confidence,
            "direction": direction,
            "price": price,
            "atr": atr,
            "reasons": reasons,
        }

    # =====================================================
    # GOOD TRADE
    # =====================================================

    # -----------------------------------------------------
    # LIMIT ENTRY
    # -----------------------------------------------------

    if direction == "BUY":

        # Pullback Buy Limit
        limit_entry = (
            price - atr * 0.35
        )

        # Do not put limit below
        # an unreasonable structure area
        if limit_entry < recent_low:

            limit_entry = (
                price - atr * 0.20
            )

        sl = (
            limit_entry
            - atr * 1.40
        )

    else:

        # Pullback Sell Limit
        limit_entry = (
            price + atr * 0.35
        )

        if limit_entry > recent_high:

            limit_entry = (
                price + atr * 0.20
            )

        sl = (
            limit_entry
            + atr * 1.40
        )

    # -----------------------------------------------------
    # TARGET SIZE
    # -----------------------------------------------------

    # Stronger confidence → larger targets
    if confidence >= 90:

        target_factor = 4.0

    elif confidence >= 85:

        target_factor = 3.0

    elif confidence >= 75:

        target_factor = 2.4

    else:

        target_factor = 1.8

    # -----------------------------------------------------
    # FX / GOLD MINIMUM 100 PIPS
    # -----------------------------------------------------

    pip = pip_size(symbol)

    if pip is not None:

        minimum_move = (
            MIN_PIPS * pip
        )

    else:

        # Crypto:
        # use ATR, not "pips"
        minimum_move = (
            atr * 2.0
        )

    # -----------------------------------------------------
    # TARGETS
    # -----------------------------------------------------

    tp1_move = max(
        atr * target_factor,
        minimum_move
    )

    tp2_move = max(
        tp1_move * 1.75,
        atr * (
            target_factor + 1.5
        )
    )

    tp3_move = max(
        tp2_move * 1.50,
        atr * (
            target_factor + 3.0
        )
    )

    if direction == "BUY":

        tp1 = (
            limit_entry
            + tp1_move
        )

        tp2 = (
            limit_entry
            + tp2_move
        )

        tp3 = (
            limit_entry
            + tp3_move
        )

    else:

        tp1 = (
            limit_entry
            - tp1_move
        )

        tp2 = (
            limit_entry
            - tp2_move
        )

        tp3 = (
            limit_entry
            - tp3_move
        )

    # -----------------------------------------------------
    # RISK / REWARD + PIPS
    # -----------------------------------------------------

    if direction == "BUY":

        risk = abs(
            limit_entry - sl
        )

        reward = abs(
            tp2 - limit_entry
        )

    else:

        risk = abs(
            sl - limit_entry
        )

        reward = abs(
            limit_entry - tp2
        )

    rr = (
        reward / risk
        if risk > 0
        else 0
    )

    # Calculate pip distances for FX / Gold / Silver.
    # Crypto does not have a universal broker pip size,
    # so these values are left as None for crypto.
    pip = pip_size(symbol)

    if pip is not None and pip > 0:
        risk_pips = round(risk / pip)
        tp1_pips = round(abs(tp1 - limit_entry) / pip)
        tp2_pips = round(abs(tp2 - limit_entry) / pip)
        tp3_pips = round(abs(tp3 - limit_entry) / pip)
    else:
        risk_pips = None
        tp1_pips = None
        tp2_pips = None
        tp3_pips = None

    return {
        "symbol": symbol,
        "market": market,
        "confidence": confidence,
        "direction": direction,
        "price": price,
        "atr": atr,
        "limit_entry": limit_entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "rr": rr,
        "risk_pips": risk_pips,
        "tp1_pips": tp1_pips,
        "tp2_pips": tp2_pips,
        "tp3_pips": tp3_pips,
        "reasons": reasons,
    }


# =========================================================
# FORMAT ANALYSIS
# =========================================================

def format_analysis(result):

    symbol = result["symbol"]

    market = result["market"]

    confidence = result["confidence"]

    direction = result["direction"]

    price = result["price"]

    if market != "GOOD":

        return (
            f"📊 {symbol}\n\n"
            f"Market: {market}\n"
            f"Confidence: {confidence}%\n"
            f"Current Price: "
            f"{format_price(price)}\n\n"
            f"⚠️ No strong trade setup yet."
        )

    limit_entry = result[
        "limit_entry"
    ]

    sl = result["sl"]
    tp1 = result["tp1"]
    tp2 = result["tp2"]
    tp3 = result["tp3"]
    rr = result["rr"]

    risk_pips = result.get("risk_pips")
    tp1_pips = result.get("tp1_pips")
    tp2_pips = result.get("tp2_pips")
    tp3_pips = result.get("tp3_pips")

    if risk_pips is not None:
        pip_text = (
            f"Risk: {risk_pips} pips\n"
            f"🎯 TP1: {tp1_pips} pips\n"
            f"🎯 TP2: {tp2_pips} pips\n"
            f"🎯 TP3: {tp3_pips} pips"
        )
    else:
        pip_text = "Pips: N/A (crypto has no universal pip size)"

    if direction == "BUY":

        action = "🟢 BUY LIMIT"

    else:

        action = "🔴 SELL LIMIT"

    reason_text = "\n".join(
        "• " + x
        for x in result["reasons"]
    )

    return (
        f"📊 {symbol}\n\n"
        f"Market: 🟢 GOOD\n"
        f"Confidence: {confidence}%\n"
        f"Signal: {action}\n\n"
        f"Current Price: {format_price(price)}\n\n"
        f"Limit Entry: {format_price(limit_entry)}\n"
        f"SL: {format_price(sl)}\n"
        f"{pip_text}\n\n"
        f"🎯 TP1: {format_price(tp1)}\n"
        f"🎯 TP2: {format_price(tp2)}\n"
        f"🎯 TP3: {format_price(tp3)}\n\n"
        f"Risk/Reward: 1:{rr:.2f}\n\n"
        f"Reasons:\n{reason_text}"
    )


# =========================================================
# TELEGRAM COMMANDS / BOT
# =========================================================

def symbol_keyboard():
    buttons = []
    for i in range(0, len(AVAILABLE_SYMBOLS), 2):
        row = []
        for symbol in AVAILABLE_SYMBOLS[i:i + 2]:
            row.append(InlineKeyboardButton(
                symbol,
                callback_data=f"symbol:{symbol}"
            ))
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            "🔎 ALL SYMBOLS",
            callback_data="scan_all"
        )
    ])
    return InlineKeyboardMarkup(buttons)


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "🤖 CryptoFlowBot is running.\n\n"
        "👇 Choose a symbol below, or press ALL SYMBOLS to scan the full configured list.\n\n"
        "You can still type a symbol manually, for example BTCUSDT or EUR/USD.",
        reply_markup=symbol_keyboard()
    )


async def send_analysis(
    message,
    symbol: str
):
    symbol = symbol.strip()
    if not symbol:
        await message.reply_text(
            "Please choose or send a symbol.",
            reply_markup=symbol_keyboard()
        )
        return

    try:
        normalized = normalize_symbol(symbol)
        df = await asyncio.to_thread(get_market_data, normalized)
        result = await asyncio.to_thread(
            analyze_market, df, normalized
        )
        text = format_analysis(result)
        await message.reply_text(
            text,
            reply_markup=symbol_keyboard()
        )
    except Exception as e:
        print(f"Analysis error for {symbol}: {e}")
        await message.reply_text(
            f"❌ Could not analyze {symbol}.\n"
            f"Error: {e}",
            reply_markup=symbol_keyboard()
        )


async def analyze_symbol(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    symbol: str
):
    await send_analysis(update.message, symbol)


async def analyze_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not context.args:
        await update.message.reply_text(
            "👇 Choose a symbol below or use: /analyze BTCUSDT",
            reply_markup=symbol_keyboard()
        )
        return

    symbol = " ".join(context.args)
    await analyze_symbol(update, context, symbol)


async def scan_all_symbols():
    results = []
    symbols = AVAILABLE_SYMBOLS[:]

    if MAX_SCAN_SYMBOLS > 0:
        symbols = symbols[:MAX_SCAN_SYMBOLS]

    for symbol in symbols:
        try:
            normalized = normalize_symbol(symbol)
            df = await asyncio.to_thread(
                get_market_data, normalized
            )
            result = await asyncio.to_thread(
                analyze_market, df, normalized
            )
            results.append(result)
        except Exception as e:
            print(f"Scan error for {symbol}: {e}")

        if SCAN_DELAY > 0:
            await asyncio.sleep(SCAN_DELAY)

    results.sort(
        key=lambda x: x.get("confidence", 0),
        reverse=True
    )
    return results


def format_scan_results(results):
    if not results:
        return (
            "🔎 ALL SYMBOLS SCAN\n\n"
            "❌ No symbols could be analyzed right now."
        )

    good = [r for r in results if r.get("market") == "GOOD"]
    selected = good[:SCAN_TOP_RESULTS] if good else results[:SCAN_TOP_RESULTS]

    lines = [
        "🔎 ALL SYMBOLS SCAN",
        "",
        f"Analyzed: {len(results)} symbols",
        f"Good setups: {len(good)}",
        "",
    ]

    if good:
        lines.append("🟢 BEST SETUPS")
    else:
        lines.append("⚠️ NO GOOD SETUP — TOP RESULTS")

    for i, r in enumerate(selected, 1):
        direction = r.get("direction", "-")
        market = r.get("market", "-")
        confidence = r.get("confidence", 0)
        symbol = r.get("symbol", "-")
        icon = "🟢" if direction == "BUY" else "🔴" if direction == "SELL" else "⚪"
        lines.append(
            f"{i}. {icon} {symbol} | {direction} | "
            f"{confidence}% | {market}"
        )

    lines.extend([
        "",
        "Tap a symbol below for the full entry / SL / TP setup."
    ])
    return "\n".join(lines)


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if query.data == "scan_all":
        await query.edit_message_text(
            "⏳ Scanning all configured symbols...\n"
            "Please wait a moment."
        )
        try:
            results = await scan_all_symbols()
            text = format_scan_results(results)
            await query.message.reply_text(
                text,
                reply_markup=symbol_keyboard()
            )
        except Exception as e:
            print(f"All-symbol scan error: {e}")
            await query.message.reply_text(
                f"❌ ALL SYMBOLS scan failed.\nError: {e}",
                reply_markup=symbol_keyboard()
            )
        return

    if query.data.startswith("symbol:"):
        symbol = query.data.split(":", 1)[1]
        await query.edit_message_text(
            f"⏳ Analyzing {symbol}..."
        )
        try:
            normalized = normalize_symbol(symbol)
            df = await asyncio.to_thread(get_market_data, normalized)
            result = await asyncio.to_thread(
                analyze_market, df, normalized
            )
            text = format_analysis(result)
            await query.message.reply_text(
                text,
                reply_markup=symbol_keyboard()
            )
        except Exception as e:
            print(f"Button analysis error for {symbol}: {e}")
            await query.message.reply_text(
                f"❌ Could not analyze {symbol}.\nError: {e}",
                reply_markup=symbol_keyboard()
            )


async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    symbol = update.message.text.strip()

    if symbol.startswith("/"):
        return

    await analyze_symbol(update, context, symbol)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing.")

    # Render needs an HTTP listener on the PORT it provides.
    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True
    )
    health_thread.start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start_command)
    )
    application.add_handler(
        CommandHandler("analyze", analyze_command)
    )
    application.add_handler(
        CallbackQueryHandler(button_handler)
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("CryptoFlowBot Telegram polling started.")
    application.run_polling()


if __name__ == "__main__":
    main()

