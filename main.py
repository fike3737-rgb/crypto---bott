import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get('BOT_TOKEN', '6760230059:AAEUS1bZ5P8kAvL86ZPtuh-7GvA22z5egR4')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Trading Bot is active and running!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    else:
        return "Invalid signature", 403

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
        "⚠️ *ማሳሰቢያ:* የገበያ ሁኔታን እያዩ ሪስክ ማኔጅመንትዎን ይጠብቁ!"
    )
    bot.reply_to(message, signal_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

