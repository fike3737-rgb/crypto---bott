import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# ቶከኑን እና ኪዩን በቀጥታ እዚህ እናስገባለን (ምንም ግጭት እንዳይፈጥር)
TELEGRAM_BOT_TOKEN = "8703693504:AAGRVPnzjB49_tHWmElWYasGuhTgCfzLMfU"
GEMINI_API_KEY = "AQ.Ab8RN6IApOru0HbLxYhnMJM_YVwq-IWs3UyVymept78ynLhyYw"

# ጀሚኒን ማዋቀር
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ቴሌግራም ቦት ማዋቀር
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# የፍላስክ ሰርቨር ማዋቀር
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

# ቴሌግራም መልዕክቶችን በ Webhook የሚቀበልበት ራውት
@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# የቴሌግራም መልዕክት ማስተናገጃ ሃንድለሮች
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
    # የቴሌግራም ዌብሁክን ከ Render URL ጋር ማገናኘት
    RENDER_URL = f"https://crypto-bott-iyf3.onrender.com/{TELEGRAM_BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL)
    
    # ሰርቨሩን ማስነሳት
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

