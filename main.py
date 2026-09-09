import os
from flask import Flask, request
import telebot

TOKEN = "8760230059:AAGjK5qt9LJUkULb3w1whmahrN8QqDYkMOQ"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().to_dict(flat=True) if hasattr(request.get_data(), 'to_dict') else request.data.decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    welcome_text = (
        "ሰላም! የትሬዲንግ ቻርት ፎቶ (TradingView, MT5) ይላኩ።\n\n"
        "በ 30m, 15m, 5m የጊዜ ማዕቀፎች ላይ በመመስረት የሚከተሉትን እናቀርባለን፦\n"
        "• **Buy / Sell** ሲግናል\n"
        "• **Entry Point** (የመግቢያ ነጥብ)\n"
        "• **Stop Loss & Take Profit** (150 - 250 Pips)\n"
        "• **Pending Orders** (Buy Limit / Sell Limit)"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['photo'])
def handle_chart_photo(message):
    signal_response = (
        "📊 **የገበያ ትንተና እና ሲግናል ውጤት:**\n\n"
        "• **Timeframe Analysis:** 30m (Trend Direction) | 15m & 5m (Execution Zone)\n"
        "• **Market Position:** **BUY / SELL (Bullish/Bearish Setup)**\n"
        "• **Entry Point (መግቢያ ነጥብ):** በወቅታዊው የገበያ የድጋፍ/መቋቋም (Support/Resistance) ዞን\n"
        "• **Pending Orders:** ተስማሚ የሆኑ Buy Limit / Sell Limit ትዕዛዞች\n"
        "• **Stop Loss (የኪሳራ ገደብ):** 150 - 250 Pips ርቀት\n"
        "• **Take Profit (የትርፍ ኢላማ):** 300 - 500 Pips\n\n"
        "⚠️ *ማሳሰቢያ:* የገበያ ሁኔታን እያዩ ሪስክ ማኔጅመንትዎን ይጠбቁ!"
    )
    bot.reply_to(message, signal_response)

if __name__ == '__main__':
    # ዌብሁክን በራስሰር ማገናኘት
    bot.remove_webhook()
    bot.set_webhook(url=f"https://crypto-bott-aj9z.onrender.com/{TOKEN}")
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

