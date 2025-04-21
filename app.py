import os
import requests
import openai
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from scraper import (
    scrape_flights_playwright,
    scrape_hotels_playwright,
    scrape_tours_playwright
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.get("/")
def home():
    return PlainTextResponse("OxfordAI is running!")

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("✅ Webhook hit!")
    print("📩 Incoming:", data)

    incoming_msg = data.get("data", {}).get("body", "")
    sender = data.get("data", {}).get("from", "")

    if not incoming_msg or not sender:
        print("⚠️ Missing message or sender")
        return PlainTextResponse("No valid message", status_code=200)

    reply = await get_gpt_response(incoming_msg)

    response = requests.post(
        f"https://api.ultramsg.com/{os.getenv('ULTRA_INSTANCE_ID')}/messages/chat",
        data={
            "token": os.getenv("ULTRA_TOKEN"),
            "to": sender,
            "body": reply
        }
    )
    print("📬 UltraMsg Response:", response.status_code, response.text)

    return PlainTextResponse("OK", status_code=200)


async def get_gpt_response(prompt):
    try:
        # Step 1: Detect type
        type_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "نوع درخواست را فقط با یکی از این گزینه‌ها مشخص کن: tour، flight یا hotel."},
                {"role": "user", "content": prompt}
            ]
        )
        request_type = type_response.choices[0].message["content"].strip().lower()
        print("🔍 Detected Type:", request_type)

        # Step 2: Scrape with Playwright
        if "flight" in request_type:
            data = scrape_flights_playwright()
        elif "hotel" in request_type:
            data = scrape_hotels_playwright()
        else:
            data = scrape_tours_playwright()

        formatted_data = "\n".join(data) or "هیچ اطلاعاتی در حال حاضر موجود نیست."

        # Step 3: Generate GPT reply
        reply_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "شما یک دستیار حرفه‌ای گردشگری هستید که به زبان فارسی به سوالات تور، هتل و پرواز پاسخ می‌دهد."},
                {"role": "user", "content": f"{prompt}\n\nاطلاعات موجود:\n{formatted_data}"}
            ],
            temperature=0.7
        )
        return reply_response.choices[0].message["content"].strip()

    except Exception as e:
        print("❌ GPT error:", e)
        return "ببخشید پرنسس.."
