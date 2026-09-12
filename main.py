import os
from telegram.ext import ApplicationBuilder

# 1. ፖርቱን ከሬንደር መቀበል
PORT = int(os.environ.get('PORT', '8443'))

# 2. የቦት ቶከን
BOT_TOKEN = "8703693504:AAE5dfXRocJZupznR2k5Xd3EecO2n8KDCfI"

# 3. application የሚለውን ተለዋዋጭ መፍጠር (እዚህ ጋር ነው የጎደለው)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# 4. ዌብሆክን ማስጀመር
application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=f"https://crypto--bott.onrender.com/{BOT_TOKEN}"
)

