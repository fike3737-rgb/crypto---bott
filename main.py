import os
import groq
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 1. ከ Render Environment Variables እንዲያነብ ማድረግ
GROQ_API_KEY = os.environ.get("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")
TELEGRAM_BOT_TOKEN = os.environ.get("8703693504:AAH8dc8T9EVG2gRlIenG9ZsDYcZtIDEw48I")
RENDER_EXTERNAL_URL = "https://crypto---bott.onrender.com"  # የሰርቨርዎ ትክክለኛ ሊንክ

client = groq.Groq(api_key=GROQ_API_KEY)

# ሞዴል በራሱ እንዲመርጥ ማድረግ
try:
    available_models = [m.id for m in client.models.list()]
    active_model = next((m for m in available_models if "llama" in m), available_models[0])
except Exception:
    active_model = "llama-3.1-8b-instant"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Analyzing '{text}'... Please wait.")
    
    try:
        response = client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "user", "content": f"Provide financial market analysis for: {text}"}
            ]
        )
        reply_text = response.choices[0].message.content
        await update.message.reply_text(reply_text)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    PORT = int(os.environ.get("PORT", 8443))
    
    print("Starting bot with Webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{RENDER_EXTERNAL_URL}/{TELEGRAM_BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()

