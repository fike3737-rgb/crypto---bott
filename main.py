import telebot

# የቦቱን ቶከን እዚህ አስገባ
TOKEN = '8760230059:AAG_e2V6H6KI8IEdnUiStrW0t_OUgSwPsDs'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "ሰላም! የክሪፕቶ እና ጎልድ ትንተና ቦትዎ በሰላም ተጀምሯል!")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, f"መልእክትዎ ደርሷል: {message.text}")

# ቦቱን ማሰኬጃ
bot.infinity_polling()
