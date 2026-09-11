import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads the .env file and loads it into environment variables

API_KEY = os.getenv("GEMINI_API_KEY")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [{
        "parts": [{"text": "Write a Python function that reverses a linked list. Only output the code, no explanation."}]
    }]
}

response = requests.post(URL, json=payload)
response.raise_for_status()

data = response.json()
generated_text = data["candidates"][0]["content"]["parts"][0]["text"]
print(generated_text)