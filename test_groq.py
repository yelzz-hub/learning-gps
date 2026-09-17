import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print("API key ditemukan:", api_key is not None)

client = Groq(
    api_key=api_key
)

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "user",
            "content": "Hello! Introduce yourself briefly."
        }
    ]
)

print(response.choices[0].message.content)