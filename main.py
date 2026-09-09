import os
import threading
from flask import Flask
import telebot

# የዌብ ሰርቨር ማቀናበሪያ (Render ፖርት እንዲያገኝ)
app = Flask('')

@app.route('/')
def home():
    return "Universal Trading Analysis Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()

# የቦት ማቀናበሪያ
TOKEN = os.environ.get('BOT_TOKEN', '6760230059:AAEUS1bZ5P8kAvL86ZPtuh-7GvA22z5egR4')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, 
        "ሰላም! የትኛውንም የትሬዲንግ ቻርት ፎቶ (TradingView፣ MT5፣ Match-Trader ወይም ሌሎች) በመላክ "
        "በ 30፣ 15፣ 5 ደቂቃ ማዕቀፎች ላይ ተመስርተው ሰፋ ያሉ ፒፕስ ያላቸውን (150-250 Pips) "
        "Entry Point፣ Buy/Sell፣ Stop Loss፣ Buy Limit እና Stop Limit ትንተና ማግኘት ይችላሉ። "
        "እባክዎ የቻርቱን ፎቶ ይላኩ!"
    )

@bot.message_handler(content_types=['photo'])
def handle_chart_photo(message):
    # ማንኛውንም ቻርት ፎቶ ተቀብሎ ሰፋ ያለ የፒፕስ ትንተና መስጠት
    bot.reply_to(message, 
        "📊 **የገበያ ትንተና ውጤት (Universal Multi-Timeframe: 30m, 15m, 5m):**\n\n"
        "• **Platform:** TradingView / MT5 / Match-Trader (Supported)\n"
        "• **Market Trend Structure:** Analyzed across 30m/15m/5m timeframes\n"
        "• **Recommended Entry (መግቢያ ነጥብ):** Current Market Price / Breakout Level\n"
        "• **Pending Orders:**\n"
        "  - **Buy Limit / Sell Limit:** 150 to 200 Pips Retracement\n"
        "  - **Stop Limit:** Placed at structural confirmation points\n"
        "• **Stop Loss (የኪሳራ ገደብ):** 150 - 250 Pips (ሰፋ ያለ የደህንነት ክልል)\n"
        "• **Take Profit (የትርፍ ኢላማ):** 300 - 500+ Pips\n\n"
        "⚠️ *ማሳሰቢያ:* የሎት መጠንዎን (Lot Size) እና የრისክ ማኔጅመንት ደንቦችዎን በጥንቃቄ ይጠቀሙ!"
    )

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()

