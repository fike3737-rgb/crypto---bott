import os
import telebot
import requests
from flask import Flask, request as flask_request

TELEGRAM_BOT_TOKEN = "8703693504:AAGID7NfYlxJG8WGTvyC_SoJhQODttmokM4"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = flask_request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "ሰላም! የፋይናንስ ማርኬት ትንታኔ ቦትዎ ዝግጁ ነው። ጽሑፍ መጻፍ ይችላሉ።")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def analyze_market_text(message):
    user_query = message.text
    bot.reply_to(message, f"'{user_query}' የገበያ ትንታኔ በመዘጋጀት ላይ ነው...")
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [{
                "parts": [{"text": f"Provide a detailed financial market analysis, technical indicators (RSI, MACD), and buy/sell levels for: {user_query}. Respond in Amharic."}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        
        # 'candidates' መኖሩን እና ባዶ አለመሆኑን ማረጋገጫ
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            candidate = res_data['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                reply_text = candidate['content']['parts'][0]['text']
                bot.reply_to(message, reply_text)
            else:
                bot.reply_to(message, "ይቅርታ, የጀሚኒ መልስ ትክክለኛ ቅርጸት የለውም።")
        else:
            # የደህንነት ማጣሪያ (Safety) ሊገድበው ሲችል የሚመጣ መልእክት
            bot.reply_to(message, f"የተገኘው ምላሽ በደህንነት ወይም በሌላ ምክንያት ታግዷል። ዝርዝር: {res_data}")
            
    except Exception as e:
        bot.reply_to(message, f"ስህተት አጋጥሟል: {str(e)}")

if __name__ == "__main__":
    RENDER_URL = f"https://crypto-bott-iyf3.onrender.com/{TELEGRAM_BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL)
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

