import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from flask import Flask, request
from openai import OpenAI

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
LOGIN_URL = "http://1to100.ir/admin/login"
USERNAME = os.getenv("OXFORD_USER")
PASSWORD = os.getenv("OXFORD_PASS")

app = Flask(__name__)

@app.route("/")
def home():
    return "OxfordAI is running!"


@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    data = request.get_json()
    print("✅ Webhook hit!")
    print("📩 Incoming:", data)

    incoming_msg = data.get("data", {}).get("body", "")
    sender = data.get("data", {}).get("from", "")

    if not incoming_msg or not sender:
        return "No valid message", 200

    reply = get_gpt_response(incoming_msg)

    requests.post(
        f"https://api.ultramsg.com/{os.getenv('ULTRA_INSTANCE_ID')}/messages/chat",
        data={
            "token": os.getenv("ULTRA_TOKEN"),
            "to": sender,
            "body": reply
        }
    )

    return "OK", 200

def get_gpt_response(prompt):
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "شما یک دستیار سفر حرفه‌ای هستید که به فارسی پاسخ می‌دهد."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT error:", e)
        return "متأسفم، مشکلی پیش آمده. لطفاً دوباره امتحان کنید."


