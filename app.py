import os
import requests
import openai
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from scraper import (
    scrape_flights_playwright,
    scrape_hotels_playwright,
    scrape_tours_playwright
)

asyncio.get_event_loop().set_debug(False)

# ─────────────────────────────────────────────
# Shared memory for user follow-up context
user_context = {}

def detect_flight_context(user_id, user_input):
    if "پرواز" in user_input and not has_date(user_input):
        user_context[user_id] = {"intent": "flight", "missing": "date", "original_msg": user_input}
        return "لطفاً تاریخ مورد نظر خود برای پرواز را مشخص کنید."
    return None

def has_date(text):
    persian_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                      "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    english_months = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december",
                      "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

    lower_text = text.lower()
    return any(month in lower_text for month in english_months) or any(month in text for month in persian_months)

def resolve_context(user_id, new_input):
    context = user_context.get(user_id)
    if context and context.get("missing") == "date":
        full_prompt = f"{context['original_msg']}، در تاریخ {new_input}"
        del user_context[user_id]
        return full_prompt
    return new_input
    

# ─────────────────────────────────────────────
# GPT & FastAPI config
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

@app.get("/")
def home():
    return PlainTextResponse("OxfordAI is running!")

from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

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

    # 👑 Booking trigger
    if "رزرو" in incoming_msg.strip():
        context = user_context.get(sender, {}).get("last_intent", "درخواست نامشخص")
        notify_human_agent(sender, context)
        log_to_sheet(sender, incoming_msg, msg_type="booking_trigger", context=context)
        return PlainTextResponse("OK", status_code=200)

    # 🧠 Flight date follow-up
    followup = detect_flight_context(sender, incoming_msg)
    if followup:
        reply = followup
        log_to_sheet(sender, incoming_msg, msg_type="flight-followup", context="waiting for date")
    else:
        full_prompt = resolve_context(sender, incoming_msg)
        reply = await get_gpt_response(full_prompt)
        log_to_sheet(sender, full_prompt, msg_type="request", context="final prompt")

    # 💌 Send reply back
    try:
        response = requests.post(
            f"https://api.ultramsg.com/{os.getenv('ULTRA_INSTANCE_ID')}/messages/chat",
            data={
                "token": os.getenv("ULTRA_TOKEN"),
                "to": sender,
                "body": reply
            }
        )
        print("📬 UltraMsg Response:", response.status_code, response.text)
    except Exception as e:
        print("🚨 UltraMsg Error:", e)

    return PlainTextResponse("OK", status_code=200)


# ─────────────────────────────────────────────
def log_to_sheet(sender, message, msg_type="unknown", context=""):
    try:
        credentials_path = "/etc/secrets/gcreds.json"
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("OxfordAI Logs")
        try:
            worksheet = sheet.worksheet("Logs")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title="Logs", rows="1000", cols="5")
            worksheet.append_row(["Timestamp", "Client Number", "Message", "Detected Type", "Context"])

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, sender, message, msg_type, context])
        print("✅ Logged to Google Sheets")
    except Exception as e:
        print("❌ Logging error:", e)

# ─────────────────────────────────────────────
def notify_human_agent(user_number, request_details):
    try:
        message = f"رزرو جدید دریافت شد:\nشماره کاربر: {user_number}\nدرخواست: {request_details}"
        response = requests.post(
            f"https://api.ultramsg.com/{os.getenv('ULTRA_INSTANCE_ID')}/messages/chat",
            data={
                "token": os.getenv("ULTRA_TOKEN"),
                "to": "+989023412100",
                "body": message
            }
        )
        print("📞 Handover sent to agent:", response.status_code)
    except Exception as e:
        print("❌ Failed to notify human agent:", e)
#-----------------------------------------------------------------------
async def get_gpt_response(prompt):
    try:
        type_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "نوع درخواست را فقط با یکی از این گزینه‌ها مشخص کن: tour، flight یا hotel."},
                {"role": "user", "content": prompt}
            ]
        )
        request_type = type_response.choices[0].message["content"].strip().lower()
        print("🔍 Detected Type:", request_type)

        if "flight" in request_type:
            data = scrape_flights_playwright()
        elif "hotel" in request_type:
            data = scrape_hotels_playwright()
        else:
            data = scrape_tours_playwright()

        formatted_data = "\n".join(data) or "هیچ اطلاعاتی در حال حاضر موجود نیست."

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
