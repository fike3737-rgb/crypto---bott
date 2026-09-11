import os
from openai import OpenAI
# Render ላይ ያስገባነውን ቁልፍ እራሱ በራሱ እንዲቀበለው ማድረግ ይቻላል
client = OpenAI(
    client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)


response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": "እርስዎ የክሪፕቶ እና የፋይናንስ ገበያ ተንታኝ ነዎት።",
        },
        {"role": "user", "content": "የተጠቃሚው ጥያቄ እዚህ ይገባል"},
    ],
)
answer = response.choices[0].message.content

