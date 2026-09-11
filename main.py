import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
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

