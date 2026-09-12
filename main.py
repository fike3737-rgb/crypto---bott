import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

PORT = int(os.environ.get('PORT', '8443'))
BOT_TOKEN = "8703693504:AAGP3Y9h2kukybDwSkYYMB4RjfaENQi_4qk"

# 1. /start ሲሉ የሚሰጠው መልስ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! የ ክሪፕቶ መረጃ ቦትዎ በስኬት ተጀምሯል።")

# 2. ተራ ጽሑፍ ሲጽፉ የሚመልሰው (በ AI ወይም በራሱ)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"የላኩትን መልዕክት ተቀብያለሁ: {user_text}")

application = ApplicationBuilder().token(BOT_TOKEN).build()

# ሃንድለሮችን መጨመር
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ዌብሆክን ማስጀመር
application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=f"https://crypto--bott.onrender.com/{BOT_TOKEN}"
)

