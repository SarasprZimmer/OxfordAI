import os
import time
import requests
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from flask import Flask, request

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

    # ✉️ Send reply via UltraMsg
    response = requests.post(
        f"https://api.ultramsg.com/{os.getenv('ULTRA_INSTANCE_ID')}/messages/chat",
        data={
            "token": os.getenv("ULTRA_TOKEN"),
            "to": sender,
            "body": reply
        }
    )
    print("📬 UltraMsg Response:", response.status_code, response.text)

    return "OK", 200

def get_gpt_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "شما یک دستیار حرفه‌ای گردشگری هستید که به زبان فارسی صحبت می‌کند. "
                        "شغل شما این است که به سوالات مربوط به تورها، هتل‌ها و پروازها پاسخ دهید. "
                        "اگر مقصد یا تاریخ مشخصی گفته شد، به صورت مودبانه و مفید پاسخ دهید."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("❌ GPT error:", e)
        return "متأسفم، مشکلی پیش آمده. لطفاً دوباره امتحان کنید."
