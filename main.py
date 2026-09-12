PORT = int(os.environ.get('PORT', '8443'))

# ቦቱ ዌብሆክን ተጠቅሞ እንዲሰራ ማድረግ
application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="8703693504:AAE5dfXRocJZupznR2k5XD3Eec02n8KDCFI",  # የቦትህ ቶከን
    webhook_url="https://crypto--bott.onrender.com/8703693504:AAE5dfXRocJZupznR2k5XD3Eec02n8KDCFI" # የሬንደር ሊንክህ ከቶከኑ ጋር
)

