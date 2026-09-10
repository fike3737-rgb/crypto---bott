import os
import telebot
import google.generativeai as genai

# Render Environment Variables - Render ላይ የተዘጋጁትን ቁልፎች ማንበቢያ
TELEGRAM_BOT_TOKEN = "8768230059:AAFDAuFHW0j77fvLdKW-Rrzilj_4E1vsBV8"
GEMINI_API_KEY = "AQ.Ab8RN6IApOru0HbLxYhnMJM_YVwq-IWs3UyVymept78ynLhyYw

# የቴሌግራም ቁልፉ መኖር እና አለመኖሩን ማረጋገጫ
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN በ Render Environment ውስጥ አልተገኘም!")

# Gemini እና Telegram Botን ማዘጋጀት
genai.configure(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# የገበያ ትንታኔ መስጫ Function
def generate_market_analysis(symbol):
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[{"google_search": {}}]
    )
    prompt = f"""
    እባክህ አሁን ያለውን የቀጥታ የገበያ ዋጋ (Real-time live price) ከኢንተርኔት ፈልገህ በማውጣት ለ {symbol} (ለ GOLD/XAUUSD, Crypto, ወይም Forex) ጥልቅ የገበያ ትንታኔ አድርግ።
    
    የሚከተሉትን ተጨማሪ ነገሮች በግልጽ እና በተደራጀ መልኩ አስቀምጥ፦
    1. 💰 **አሁን ያለው የቀጥታ ዋጋ (Current Live Price)**
    2. 📊 **የገበያ አቅጣጫ (BUY / SELL / HOLD)**
    3. 🎯 **የሚመከሩ Take Profit (TP) ደረጃዎች** (TP1, TP2, TP3)
    4. 🛡️ **የሚመከር Stop Loss (SL) ደረጃ**
    5. ⚖️ **Risk-to-Reward Ratio**
    6. 🧱 **የድጋፍ እና የመቋቋሚያ ደረጃዎች (Key Support & Resistance Levels)**
    7. 📝 **የቴክኒካል እና የፋንዳሜንታል ትንታኔ አጭር ማብራሪያ (በአማርኛ)**
    
    መልስህን በአማርኛ ቋንቋ፣ በግልጽ እና በምልክቶች (Emojis) አምረው አቅርበው።
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ይቅርታ፣ ትንታኔውን በማዘጋጀት ላይ ስህተት ተፈጥሯል፦ {str(e)}"

# /start Command
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    welcome_text = (
        f"ሰላም {user_first_name}! 👋\n\n"
        f"እንኳን ወደ **የተሟላ የገበያ ትንታኔ ቦት** በደህና መጡ!\n\n"
        f"📌 **እንዴት መጠቀም ይችላሉ?**\n"
        f"የሚፈልጉትን የ Asset ስም ይላኩ (ለምሳሌ፦ `GOLD`, `BTCUSD`, `EURUSD`)"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# Message Handler
@bot.message_handler(func=lambda message: True)
def analyze_market(message):
    symbol = message.text.upper().strip()
    user_name = message.from_user.first_name
    
    wait_message = bot.reply_to(
        message, 
        f"እሺ {user_name}👨‍💻! ለ **{symbol}** የቀጥታ ዋጋ እና ተጨማሪ ቴክኒካል መረጃዎችን እየሰበሰብኩ ነው... እባክዎ ትንሽ ይጠብቁ ⏳"
    )
    
    analysis_result = generate_market_analysis(symbol)
    bot.delete_message(message.chat.id, wait_message.message_id)
    
    final_response = (
        f"👤 **ተጠቃሚ፦** {user_name}\n"
        f"🪙 **የተመረጠው የገበያ አይነት፦** {symbol}\n"
        f"-----------------------------------\n\n"
        f"{analysis_result}"
    )
    bot.reply_to(message, final_response, parse_mode="Markdown")

if __name__ == "__main__":
    print("ቦቱ በሰላም ስራ ጀምሯል...")
    bot.infinity_polling()

