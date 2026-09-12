import os
import threading
from flask import Flask
import telebot
from groq import Groq

# ትክክለኛውን የቦት ቶከን እና የ Groq ኪይ እዚህ ያስገቡ
TELEGRAM_BOT_TOKEN = "8703693504:AAFWX9j2tp5M2tTjfXeHL2U1R5N4DAW0PtI"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

app = Flask(__name__)

# ሬንደር ፖርቱን እንዲያገኘው ዌብ ሰርቪስ ራውት
@app.route('/')
def home():
    return "Bot is running live!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Bot is ready. Send a market name like 'Gold' or 'BTC'.")

@bot.message_handler(func=lambda message: True)
def analyze_market(message):
    user_query = message.text
    bot.reply_to(message, f"Analyzing '{user_query}'... Please wait.")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Provide a detailed financial market analysis and technical levels for: {user_query}. Respond in English.",
                }
            ],
            model="llama-3.1-8b-instant",
        )
        response_text = chat_completion.choices[0].message.content
        bot.reply_to(message, response_text)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# ቦቱን ከበስተጀርባ በክር (Thread) ማስኬጃ
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # ቴሌግራም ቦቱን ከፍላስክ ጋር በአንድ ላይ እናስጀምራለን (Webhook አያስፈልግም)
    t = threading.Thread(target=run_bot)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

