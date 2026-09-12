import os
from flask import Flask
import telebot
from groq import Groq

TELEGRAM_BOT_TOKEN = "8703693504:AAGID7NfYlxJG8WGTvyC_SoJhQODttmokM4"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Web Service is active and running!"

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
            model="llama3-8b-8192",
        )
        response_text = chat_completion.choices[0].message.content
        bot.reply_to(message, response_text)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

if __name__ == "__main__":
    # Render የሚሰጠውን ፖርት በራስ ሰር እንዲወስድ ይደረጋል
    port = int(os.environ.get("PORT", 10000))
    
    # ቴሌግራም ፖሊንግን በሌላ ፕሬድ (Thread) ማስጀመር ይቻላል ወይም 
    # ለዌብ ሰርቪስ በአስተማማኝ ሁኔታ ዌብሁክ (Webhook) መጠቀም ይመረጣል
    # ነገር ግን አሁን ሰርቨሩ እንዲነቃ ፍላስክ ብቻውን ይሮጣል
    app.run(host="0.0.0.0", port=port)

