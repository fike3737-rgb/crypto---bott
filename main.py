import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# የቦት ቶከን እና የጀሚኒ ኪይ
TELEGRAM_BOT_TOKEN = "8703693504:AAG4nSGyYrOk6Hn5yy7muL0SENh08jxRiKk"
GEMINI_API_KEY = "AQ.Ab8RN6IApOru0HbLxYhnMJM_YVwq-IWs3UyVymept78ynLhyYw"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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

# 1. የጽሑፍ መልዕክቶችን ብቻ ሲልኩ የሚሰራ ክፍል
@bot.message_handler(func=lambda message: True, content_types=['text'])
def analyze_market_text(message):
    user_query = message.text
    bot.reply_to(message, f"'{user_query}' የገበያ ትንታኔ በመዘጋጀት ላይ ነው፣ እባክዎ ትንሽ ይጠብቁ...")
    try:
        prompt = f"Provide a detailed financial market analysis, technical indicators (RSI, MACD), and buy/sell levels for: {user_query}. Respond in Amharic."
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "ይቅርታ፣ ትንታኔውን ማዘጋጀት አልተቻለም። እባክዎ ትንሽ ቆይተው እንደገና ይሞክሩ።")

# 2. ፎቶ እና ጽሑፍ (Caption) በአንድ ላይ ሲልኩ የሚሰራ ክፍል (ያንዳች ተጨማሪ ላይብረሪ)
@bot.message_handler(content_types=['photo'])
def handle_photo_with_caption(message):
    user_caption = message.caption if message.caption else "Analyze this financial chart"
    bot.reply_to(message, f"ፎቶው እና ጽሑፉ ደርሰዋል! '{user_caption}' በሚለው መሰረት ትንታኔ በመዘጋጀት ላይ ነው...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "chart_caption.jpg"
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # ፋይሉን በቀጥታ ለጀሚኒ multimodal ማስተላለፍ
        sample_file = genai.upload_file(path=image_path)
        
        prompt = f"User instruction: {user_caption}. Provide a detailed financial market analysis, support/resistance levels, and recommendations based on this chart and instruction. Respond in Amharic."
        response = model.generate_content([sample_file, prompt])
        
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "ይቅርታ፣ የፎቶውን እና የጽሑፉን ትንታኔ ማዘጋጀት አልተቻለም። እባክዎ እንደገና ይሞክሩ።")

if __name__ == "__main__":
    RENDER_URL = f"https://crypto-bott-iyf3.onrender.com/{TELEGRAM_BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL)
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

