import os
from flask import Flask
from threading import Thread
import telebot
from groq import Groq

# ቶከኖቹን እዚህ ያስገቡ
TELEGRAM_BOT_TOKEN = "8703693504:AAGID7NfYlxJG8WGTvyC_SoJhQODttmokM4"
GROQ_API_KEY = "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"

# Groq ማዋቀር
client = Groq(api_key=GROQ_API_KEY)

# ቴሌግራም ቦት ማዋቀር
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# የፍላስክ ሰርቨር
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# የቴሌግራም መልዕክት መቀበያ
@bot.message_handler(commands=['start'])
def send_welcome(welcome_message):
    bot.reply_to(welcome_message, "ሰላም! የፋይናንስ ማርኬት ትንታኔ ቦትዎ በGroq ዝግጁ ነው። እንደ 'Gold' ወይም 'BTC' ያሉትን ስሞች በመጻፍ ትንታኔ ማግኘት ይችላሉ።")

@bot.message_handler(func=lambda message: True)
def analyze_market(message):
    user_query = message.text
    bot.reply_to(message, f"'{user_query}' የገበያ ትንታኔ በGroq በመዘጋጀት ላይ ነው፣ እባክዎ ትንሽ ይጠብቁ...")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Provide a detailed financial market analysis, technical indicators (RSI, MACD), and buy/sell levels for: {user_query}. Respond in Amharic.",
                }
            ],
            model = "llama-3.1-8b-instant",
        )
        response_text = chat_completion.choices[0].message.content
        bot.reply_to(message, response_text)
    except Exception as e:
        bot.reply_to(message, f"ይቅርታ፣ ትንታኔውን ማዘጋጀት አልተቻለም። ስህተት: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("ቦቱ በሰላም ስራ ጀምሯል...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

