from groq import Groq

client = Groq(
    api_key="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"
)

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {
            "role": "system",
            "content": "አንተ የክሪፕቶ ተንታኝ እና የፋይናንስ ገበያ ተንታኝ ነህ።"
        },
        {
            "role": "user",
            "content": "የተጠቃሚው ጥያቄ እዚህ አለ።"
        }
    ]
)

print(response.choices[0].message.content)

