import os
from flask import Flask
from threading import Thread
import telebot
import google.generativeai as genai

# Render ፖርት ፈልጎ እንዳይዘጋ የዌብ ሰርቨር ማቋቋሚያ
app = Flask('')

@app.route('/')
def home():
    return "Bot is running live!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# Environment Variables
TELEGRAM_BOT_TOKEN = os.environ.get("8760230059:AAFLTDZjIrigBf4YSf_NWl0Qg1WbRldA4rY")
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6IApOru0HbLxYhnMJM_YVwq-IWs3UyVymept78ynLhyYw")

genai.configure(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

SYSTEM_PROMPT = """
እርስዎ ልምድ ያካበቱ የፋይናንስ ማርኬት አናሊስት ነዎት። 
ለማንኛውም የተጠየቁት አሴት (GOLD, Crypto, Forex) በበሰለ መልኩ የሚከተሉትን አካተው በአማርኛ መልስ ይስጡ፡
1. Trend & Candlestick Analysis (የገበያው አቅጣጫ እና የካንደልስቲክ ቅርፅ)
2. Technical Indicators (RSI, MACD)
3. Support and Resistance Levels
4. Pending Order Zones (Buy Limit / Sell Limit ከነ Entry, TP, SL እና Risk-to-Reward)
"""

@bot.message_handler(func=lambda message: True)
def analyze_market(message):
    try:
        user_query = message.text
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        response = model.generate_content(f"ለዚህ አሴት ዝርዝር የገበያ ትንታኔ ስጥ፡ {user_query}")
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"ስህተት ተከሰተ፡ {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("ቦቱ በሰላም ስራ ጀምሯል...")
    bot.infinity_polling()

