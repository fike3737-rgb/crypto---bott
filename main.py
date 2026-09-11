from groq import Groq

client = Groq(
    api_key="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"
)

response = client.chat.completions.create(
    model="llama3-8b-8192",
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

