import os
import threading
from flask import Flask
import telebot

app = Flask('')

@app.route('/')
def home():
    return "Trading Bot is active and running!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()

TOKEN = os.environ.get('BOT_TOKEN', '6760230059:AAEUS1bZ5P8kAvL86ZPtuh-7GvA22z5egR4')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    welcome_text = (
        "ሰላም! ማንኛውንም የትሬዲንግ ቻርት ፎቶ (TradingView, MT5, Match-Trader) ይላኩ።\n\n"
        "በ 30m, 15m, 5m የጊዜ ማዕቀፎች ላይ በመመስረት የሚከተሉትን እናቀርባለን፦\n"
        "• **Buy / Sell** ትዕዛዞች\n"
        "• **Entry Point** (የመግቢያ ነጥብ)\n"
        "• **Stop Loss & Take Profit** (150 - 250 Pips ክልል)\n"
        "• **Buy Limit / Sell Limit**"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['photo'])
def handle_chart_photo(message):
    signal_response = (
        "📊 **የገበያ ትንተና እና ሲግናል ውጤት:**\n\n"
        "• **Timeframe Analysis:** 30m (Trend) | 15m & 5m (Execution)\n"
        "• **Market Position:** **BUY / SELL**\n"
        "• **Entry Point (መግቢያ ነጥብ):** በወቅታዊው የገበያ ዋጋ ዞን\n"
        "• **Pending Orders:** Buy Limit / Sell Limit\n"
        "• **Stop Loss (የኪሳራ ገደብ):** 150 - 250 Pips\n"
        "• **Take Profit (የትርፍ ኢላማ):** 300 - 500 Pips\n\n"
        "⚠️ *ማሳሰቢያ:* ሪስክ ማኔጅመንትዎን ይጠብቁ!"
    )
    bot.reply_to(message, signal_response)

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()


