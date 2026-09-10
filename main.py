import os
from flask import Flask
from threading import Thread
import telebot
import google.generativeai as genai

# 1. ቶከኖች ከ Environment Variables ማንበብ
TELEGRAM_BOT_TOKEN = os.environ.get("8760230059:AAFLTDZjIrigBf4YSf_NWl0Qg1WbRldA4rY")
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6IApOru0HbLxYhnMJM_YVwq-IWs3UyVymept78ynLhyYw")

# 2. ጀሚኒን ማዋቀር
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. ቴሌግራም ቦት ማዋቀር
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# 4. የፍላስክ ሰርቨር (Render Port Timeout እንዳይፈጥር)
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 5. የቴሌግራም መልዕክት መቀበያ
@bot.message_handler(commands=['start'])
def send_welcome(welcome_message):
    bot.reply_to(welcome_message, "ሰላም! የፋይናንስ ማርኬት ትንታኔ ቦትዎ ዝግጁ ነው። እንደ 'Gold' ወይም 'BTC' ያሉትን ስሞች በመጻፍ ትንታኔ ማግኘት ይችላሉ።")

@bot.message_handler(func=lambda message: True)
def analyze_market(message):
    user_query = message.text
    bot.reply_to(message, f"'{user_query}' የገበያ ትንታኔ በመዘጋጀት ላይ ነው፣ እባክዎ ትንሽ ይጠብቁ...")
    
    try:
        prompt = f"Provide a detailed financial market analysis, technical indicators (RSI, MACD), and buy/sell levels for: {user_query}. Respond in Amharic."
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "ይቅርታ፣ ትንታኔውን ማዘጋጀት አልተቻለም። እባክዎ ትንሽ ቆይተው እንደገና ይሞክሩ።")

if __name__ == "__main__":
    keep_alive()
    print("ቦቱ በሰላም ስራ ጀምሯል...")
    bot.infinity_polling(skip_pending=True, timeout=90, long_polling_timeout=90)

