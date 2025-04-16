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
        # 🧠 Step 1: Use GPT to detect request type
        detection = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "فقط مشخص کن که این پیام درباره کدام یک از موارد زیر است: tour, hotel یا flight"},
                {"role": "user", "content": prompt}
            ]
        )
        req_type = detection.choices[0].message["content"].strip().lower()
        print("🔍 Detected Type:", req_type)

        # 🧹 Step 2: Scrape data based on type
        driver = get_admin_driver()
        login_admin(driver)

        if "flight" in req_type:
            data_list = scrape_flights_selenium(driver)
        elif "hotel" in req_type:
            data_list = scrape_hotels_selenium(driver)
        else:
            data_list = scrape_tours_selenium(driver)

        driver.quit()

        scraped_info = "\n".join(data_list) or "هیچ داده‌ای یافت نشد."

        # 💬 Step 3: Ask GPT to respond with scraped info
        final_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "شما یک دستیار گردشگری هستید که به زبان فارسی به سوالات مربوط به تورها، پروازها و هتل‌ها پاسخ می‌دهد."
                    )
                },
                {"role": "user", "content": f"{prompt}\n\nاطلاعات موجود:\n{scraped_info}"}
            ]
        )

        return final_response.choices[0].message["content"].strip()

    except Exception as e:
        print("❌ GPT error:", e)
        return "متأسفم، مشکلی پیش آمده. لطفاً دوباره امتحان کنید."

