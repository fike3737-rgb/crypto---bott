import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. የቦት ቶከን እና የጀሚኒ ኪይ
TELEGRAM_BOT_TOKEN = "8703693504:AAGID7NfYlxJG8WGTvyC_SoJhQODttmokM4"
GEMINI_API_KEY = "AQ.Ab8RN6IApOru0HbLxYhnMJM_YVwq-IWs3UyVymept78ynLhyYw"

genai.configure(api_key=GEMINI_API_KEY)

# 2. ቦቱን እና ፍላስክ ሰርቨሩን ማስጀመር (ይህ ነበር የጎደለው)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "ሰላም! የፋይናንስ ማርኬት ትንታኔ ቦትዎ ዝግጁ ነው። ጽሑፍ መጻፍ ወይም ፎቶ ከነ ሐሳቡ (Caption) አብሮ መላክ ይችላሉ።")

# 3. የጽሑፍ ማርኬት ትንታኔ ክፍል
@bot.message_handler(func=lambda message: True, content_types=['text'])
def analyze_market_text(message):
    user_query = message.text
    bot.reply_to(message, f"'{user_query}' የገበያ ትንታኔ በመዘጋጀት ላይ ነው፣ እባክዎ ትንሽ ይጠብቁ...")
    try:
        generation_model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Provide a detailed financial market analysis, technical indicators (RSI, MACD), and buy/sell levels for: {user_query}. Respond in Amharic."
        response = generation_model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"ስህተት አጋጥሟል: {str(e)}")

if __name__ == "__main__":
    RENDER_URL = f"https://crypto-bott-iyf3.onrender.com/{TELEGRAM_BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL)
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

