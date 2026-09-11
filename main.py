@bot.message_handler(func=lambda message: True, content_types=['text'])
def analyze_market_text(message):
    user_query = message.text
    bot.reply_to(message, f"'{user_query}' የገበያ ትንታኔ በመዘጋጀት ላይ ነው፣ እባክዎ ትንሽ ይጠብቁ...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        generation_model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"Provide a detailed financial market analysis, technical indicators (RSI, MACD), and buy/sell levels for: {user_query}. Respond in Amharic."
        response = generation_model.generate_content(prompt)
        
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"ስህተት አጋጥሟል: {str(e)}")

