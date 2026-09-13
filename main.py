import os
import time

from flask import Flask, request
import telebot
from groq import Groq


# =========================
# Environment Variables
# =========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Render automatically provides this hostname
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

# Optional custom URL
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")


# =========================
# Check Configuration
# =========================

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing")


# =========================
# Initialize
# =========================

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

app = Flask(__name__)


# =========================
# Home / Health Check
# =========================

@app.route("/", methods=["GET"])
def home():
    return "Crypto AI Bot is running with Webhook!", 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


# =========================
# Telegram Webhook
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_string = request.get_data().decode("utf-8")

        update = telebot.types.Update.de_json(json_string)

        bot.process_new_updates([update])

        return "OK", 200

    except Exception as e:
        print("Webhook error:", e)
        return "Webhook Error", 500


# =========================
# Telegram Commands
# =========================

@bot.message_handler(commands=["start"])
def start_command(message):
    bot.reply_to(
        message,
        "🤖 Welcome to Crypto AI Bot!\n\n"
        "Send me a market question and I will analyze it."
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(
        message,
        "📚 Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n\n"
        "You can also send a market question directly."
    )


# =========================
# AI Market Analysis
# =========================

@bot.message_handler(func=lambda message: True)
def analyze_market(message):
    user_query = message.text

    if not user_query:
        return

    bot.reply_to(
        message,
        "🔍 Analyzing your question... Please wait."
    )

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial market analysis assistant. "
                        "Provide educational market analysis in English. "
                        "Discuss trends, support, resistance, risk management, "
                        "and possible bullish or bearish scenarios. "
                        "Do not guarantee profits. "
                        "Do not present financial advice as certainty."
                    )
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )

        response_text = completion.choices[0].message.content

        if not response_text:
            response_text = "No analysis was returned."

        # Telegram messages have a length limit
        if len(response_text) > 4000:
            response_text = response_text[:4000]

        bot.reply_to(message, response_text)

    except Exception as e:
        print("AI Error:", e)

        bot.reply_to(
            message,
            "❌ Sorry, an error occurred while analyzing your question."
        )


# =========================
# Set Webhook
# =========================

def set_webhook():
    time.sleep(5)

    if RENDER_EXTERNAL_URL:
        base_url = RENDER_EXTERNAL_URL.rstrip("/")
    elif RENDER_EXTERNAL_HOSTNAME:
        base_url = "https://" + RENDER_EXTERNAL_HOSTNAME
    else:
        print("ERROR: Render URL or hostname is missing")
        return

    webhook_url = base_url + "/webhook"

    try:
        bot.remove_webhook()
        time.sleep(1)

        result = bot.set_webhook(url=webhook_url)

        print("===================================")
        print("Webhook URL:", webhook_url)
        print("Webhook set result:", result)
        print("===================================")

    except Exception as e:
        print("Webhook setup error:", e)


# =========================
# Start Application
# =========================

if __name__ == "__main__":

    # Set webhook before starting Flask
    set_webhook()

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
