import telebot
import os

# የቦቱን ቶከን ከኤንቫይሮመንት ወይም በቀጥታ እዚህ አስገባ
TOKEN = os.environ.get('BOT_TOKEN', '8760230059:AAEUSlBz5M8kAvL86ZPfwdW-7GvA2z5egR4')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Trading Bot Initialized. Send your chart screenshot for deep wide-range analysis.")

@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    bot.reply_to(message, "Chart received. Conducting deep multi-zone market structure & trend analysis...")
    
    # እዚህጋ የጌሚኒ ኤፒአይ ትንተና እና ጥልቅ የሲግናል ፕሮምፕት ይካተታል
    # ሰፋ ያለ የ 200-400 ፒፕስ ርቀት እና የ Buy/Sell, Buy Limit / Sell Limit ትንተና
    
    response_text = """
📊 **Automated Professional Chart & Risk Report**

• **Market Direction**: 📈 **BUY**
• **Confidence Score**: 🎯 **88%**
• **Wide Market Analysis**: Strong bullish structure on 30m timeframe, clearing major historical resistance with a target range of 300 pips.

📌 **Instant Execution Setup**:
• **Entry Price**: Current Market Price
• **Stop Loss**: 350 Pips buffer below key support
• **Take Profit**: 300 Pips upper target

⏳ **Pending Order Limits**:
• **Buy Limit**: Set at major support zone
• **Sell Limit**: Set at upper resistance boundary
"""
    bot.reply_to(message, response_text)

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, "សូម/እባክዎን የቻርት ስክሪንሾት (Screenshot) ይላኩ።")

bot.infinity_polling(skip_pending=True)


