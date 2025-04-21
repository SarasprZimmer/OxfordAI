import os
import requests
import openai
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from scraper import (
    scrape_flights_playwright,
    scrape_hotels_playwright,
    scrape_tours_playwright
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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
        print("⚠️ Missing message or sender")
        return "No valid message", 200

    reply = get_gpt_response(incoming_msg)

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
        # Step 1: Detect request type (flight, hotel, tour)
        type_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "فقط نوع درخواست را با یکی از این سه گزینه پاسخ بده: tour، flight، hotel."
                },
                {"role": "user", "content": prompt}
            ]
        )
        request_type = type_response.choices[0].message["content"].strip().lower()
        print("🔍 Detected Type:", request_type)

        # Step 2: Scrape data based on type using Playwright
        if "flight" in request_type:
            data = scrape_flights_playwright()
        elif "hotel" in request_type:
            data = scrape_hotels_playwright()
        elif "tour" in request_type:
            data = scrape_tours_playwright()
        else:
            data = ["درخواست شما قابل شناسایی نبود. لطفاً دوباره تلاش کنید."]

        formatted_data = "\n".join(data) or "هیچ اطلاعاتی در حال حاضر موجود نیست."

        # Step 3: Generate GPT response with context
        reply_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "شما یک دستیار حرفه‌ای گردشگری هستید که به زبان فارسی به سوالات مربوط به تور، هتل و پرواز پاسخ می‌دهد."
                    )
                },
                {"role": "user", "content": f"{prompt}\n\nاطلاعات موجود:\n{formatted_data}"}
            ],
            temperature=0.7
        )
        return reply_response.choices[0].message["content"].strip()

    except Exception as e:
        print("❌ GPT error:", e)
        return "ببخشید پرنسس، هنوز کدت کار نمیکنه"
