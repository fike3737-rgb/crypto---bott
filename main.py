import os
from flask import Flask, request
import telebot
import google.generativeai as genai

# የቦት እና የ AI ማዋቀሪያ
TOKEN = "8760230059:AAGjK5qt9LJUkULb3w1whmahrN8QqDYkMOQ"
bot = telebot.TeleBot(TOKEN)

# የ Google Gemini API ኪ ቁልፍ (በ Render Environment Variables ውስጥ GOOGLE_API_KEY ብለህ ማስገባት አለብህ)
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

app = Flask(__name__)


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "ሰላም! 📈 የትሬዲንግ ቻርት ፎቶ ላኩልኝ፤ AI በመጠቀም ቻርቱን በመተንተን ትክክለኛውን Entry, Stop Loss (SL) እና Take"
      " Profit (TP) ዋጋዎች አዘጋጅቼ እሰጥዎታለሁ።",
  )


@bot.message_handler(content_types=["photo"])
def handle_chart_photo(message):
  try:
    bot.reply_to(
        message,
        "🔍 ቻርቱ በ AI እየተተነተነ ነው... እባክዎ ትንሽ ይጠብቁ።",
    )

    # ፎቶውን ከቴሌግራም ማውረድ
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_path = "chart.jpg"
    with open(image_path, "wb") as new_file:
      new_file.write(downloaded_file)

    # ፎቶውን ለ Gemini AI መላክ እና ትንተና መጠየቅ
    with open(image_path, "rb") as f:
      image_bytes = f.read()

    ai_model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        "ይህንን የትሬዲንግ ቻርት በጥንቃቄ ተመልከት። የገበያውን አዝማሚያ (Trend) በመለየት "
        "የሚከተሉትን ትክክለኛ መረጃዎች በግልጽ አውጣ፦\n"
        "1. Asset / Pair (የገበያ አይነት)\n"
        "2. Signal (BUY ወይም SELL)\n"
        "3. Entry Price (ትክክለኛ የመግቢያ ዋጋ በቁጥር)\n"
        "4. Stop Loss (SL) (የጥንቃቄ ማቆሚያ ዋጋ በቁጥር)\n"
        "5. Take Profit (TP) (የትርፍ ማግኛ ዋጋ በቁጥር)\n"
        "መልስህን በአጭር እና ግልጽ በሆነ የቴሌግራም Markdown формат አቅርብ።"
    )

    response = ai_model.generate_content([
        {"mime_type": "image/jpeg", "data": image_bytes},
        prompt,
    ])

    bot.reply_to(message, response.text, parse_mode="Markdown")

  except Exception as e:
    bot.reply_to(
        message,
        f"❌ ስህተት ተፈጥሯል: ቻርቱን ማንበብ አልተቻለም። እባክዎ የ API ቁልፍ መኖሩን ያረጋግጡ።",
    )


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
  json_string = request.get_data().decode("utf-8")
  update = telebot.types.Update.de_json(json_string)
  bot.process_new_updates([update])
  return "!", 200


@app.route("/")
def index():
  return "Trading Bot with AI Vision is running live!", 200


if __name__ == "__main__":
  bot.remove_webhook()
  bot.set_webhook(url=f"https://crypto-bott-qj9z.onrender.com/{TOKEN}")

  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)

