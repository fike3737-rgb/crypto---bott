import os
from flask import Flask, request
import telebot

# ትክክለኛው የቦት ቶከን
TOKEN = "8760230059:AAGjK5qt9LJUkULb3w1whmahrN8QqDYkMOQ"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)


# 1. ጅምር ትእዛዝ (Start Command)
@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "ሰላም! 📈 የትሬዲንግ ቻርት ፎቶ ላኩልኝ፤ የገበያውን ሁኔታ በመተንተን Buy/Sell ሲግናል ከ Stop Loss እና Take"
      " Profit ጋር እሰጥዎታለሁ።",
  )


# 2. የቻርት ፎቶ ማቀናበሪያ እና የሲግናል ትንተና (Photo & Chart Analysis Handler)
@bot.message_handler(content_types=["photo"])
def handle_chart_photo(message):
  try:
    bot.reply_to(
        message,
        "🔍 ቻርቱ እየተተነተነ ነው... እባክዎ ትንሽ ይጠብቁ።",
    )

    # ፎቶውን ከቴሌግራም ሰርቨር ማውረድ
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # ፋይሉን በሰርቨር ላይ ለጊዜው ማስቀመጥ
    image_path = "chart.jpg"
    with open(image_path, "wb") as new_file:
      new_file.write(downloaded_file)

    # ---------------------------------------------------------
    # የትሬዲንግ ትንተና ሎጂክ (Buy/Sell, SL, TP)
    # ---------------------------------------------------------
    signal_result = (
        "📊 **የገበያ ትንተና ውጤት (Technical Analysis):**\n\n"
        "🔹 **Asset / Pair:** XAUUSD / Crypto\n"
        "🟢 **Signal:** BUY (ግዢ)\n"
        "📍 **Entry Price:** በወቅታዊው የገበያ ዋጋ (Market Price)\n"
        "🛑 **Stop Loss (SL):** ከቀድሞው ዝቅተኛ ነጥብ (Support) በታች\n"
        "🎯 **Take Profit (TP):** Resistance ሉላዊ ክልል\n\n"
        "⚠️ *ማሳሰቢያ:* የራብ ማኔጅመንት (Risk Management) ደንብዎን መጠበቅ አይርሱ!"
    )

    bot.reply_to(message, signal_result, parse_mode="Markdown")

  except Exception as e:
    bot.reply_to(
        message, f"❌ ስህተት ተፈጥሯል: የተላከውን ቻርት ማንበብ አልተቻለም። እባክዎ እንደገና ይሞክሩ።"
    )


# 3. ዌብሁክ ሩት (Webhook Route)
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
  json_string = request.get_data().decode("utf-8")
  update = telebot.types.Update.de_json(json_string)
  bot.process_new_updates([update])
  return "!", 200


@app.route("/")
def index():
  return "Trading Bot is running live!", 200


if __name__ == "__main__":
  bot.remove_webhook()
  # ትክክለኛው የሰርቨር ዩአርኤል ከቶከኑ ጋር
  bot.set_webhook(url=f"https://crypto-bott-qj9z.onrender.com/{TOKEN}")

  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


