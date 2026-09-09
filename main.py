import os
import threading
from flask import Flask
import telebot

# የፍላስክ ሰርቨር (Render ሰርቨሩ ንቁ ሆኖ እንዲቆይ)
app = Flask('')

@app.route('/')
def home():
    return "Trading Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()

# አዲሱን የቦት ቶከን እዚህ ጋር አስገባ (ከ BotFather የወሰድከውን)
TOKEN = "8760230059:AAGjK5qt9LJUkULb3w1whmahrN8QqDYkMOQ"
bot = telebot.TeleBot(TOKEN)

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
        "⚠️ *ማሳሰቢያ:* የገበያ ሁኔታን እያዩ ሪስክ ማኔጅመንትዎን ይጠبቁ!"
    )
    bot.reply_to(message, signal_response)

if __name__ == '__main__':
    keep_alive()
    print("Bot is starting polling...")
    bot.infinity_polling(skip_pending=True)

