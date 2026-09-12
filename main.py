import os
import groq
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 1. የ Groq API ኪ (API Key) እና የቴሌግራም ቶከን እዚህ ያስገቡ
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8703693504:AAFWX9j2tp5M2tTjfXeHL2U1R5N4DAW0PtI"

# 2. የ Groq ክላይንት ማዋቀር
client = groq.Groq(api_key=GROQ_API_KEY)

# 3. አሁን የሚሠራውን ሞዴል በራሱ በሰርቨሩ ላይ ቃኝቶ እንዲወስድ ማድረግ (Model Not Found ስህተትን ለማስቀረት)
try:
    available_models = [m.id for m in client.models.list()]
    active_model = next((m for m in available_models if "llama" in m), available_models[0])
except Exception:
    active_model = "llama-3.1-8b-instant"

# 4. መልዕክት ሲመጣ የሚሰራው ዋናው ክፍል
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Analyzing '{text}'... Please wait.")
    
    try:
        # 5. ትንታኔውን ለማግኘት Groqን መጠየቅ (በራሱ active_model ይጠቀማል)
        response = client.chat.completions.create(
            model=active_model,  # <-- ራሱ አሁን የሚሠራውን ሞዴል ይመርጣል
            messages=[
                {"role": "user", "content": f"Provide financial market analysis for: {text}"}
            ]
        )
        reply_text = response.choices[0].message.content
        await update.message.reply_text(reply_text)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# 6. ቦቱን ማስጀመር
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

