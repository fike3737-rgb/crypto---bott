import os
from flask import Flask, request
import telebot
from groq import Groq

TELEGRAM_BOT_TOKEN = "8703693504:AAGID7NfYlxJG8WGTvyC_SoJhQODttmokM4"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def home():
    return "Bot is running with Webhook!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "ሰላም! የፋይናንስ ማርኬት ትንታኔ ቦትዎ በWebhook ዝግጁ ነው።")

@bot.message_handler(func=lambda message: True)
def analyze_market(message):
    user_query = message.text
    bot.reply_to(message, f"'{user_query}' የገበያ ትንታኔ በGroq በመዘጋጀት ላይ ነው...")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Provide a detailed financial market analysis and buy/sell levels for: {user_query}. Respond in Amharic.",
                }
            ],
            model="llama-3.1-8b-instant",
        }
        bot.reply_to(message, chat_completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"ስህተት ተፈጥሯል: {str(e)}")

if __name__ == "__main__":
    # ሬንደር የሚሰጠውን ዩአርኤል እዚህ ማገናኘት ይቻላል
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

