import os
import requests
import openai
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

from scraper import (
    scrape_flights_playwright,
    scrape_hotels_playwright,
    scrape_tours_playwright
)

# ─────── LOAD ENV ───────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
user_context = {}
asyncio.get_event_loop().set_debug(False)

# ─────── CONTEXT LOGIC ───────
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

# ─────── LOGGING ───────
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

# ─────── NOTIFY AGENT ───────
def notify_human_agent(user_number, request_summary):
    try:
        message = f"📢 رزرو جدید:\nشماره: {user_number}\nدرخواست: {request_summary}"
        requests.post(
            f"https://api.ultramsg.com/{os.getenv('ULTRA_INSTANCE_ID')}/messages/chat",
            data={
                "token": os.getenv("ULTRA_TOKEN"),
                "to": "+989023412100",
                "body": message
            }
        )
        print("📲 Human agent notified")
    except Exception as e:
        print("🚨 Failed to notify agent:", e)

# ─────── WEBHOOK ───────
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
        return PlainTextResponse("No valid message", status_code=200)

    # رزرو trigger
    if "رزرو" in incoming_msg.strip():
        context = user_context.get(sender, {}).get("last_prompt", "درخواست نامشخص")
        notify_human_agent(sender, context)
        return PlainTextResponse("OK", status_code=200)

    # Handle missing date context
    followup = detect_flight_context(sender, incoming_msg)
    if followup:
        reply = followup
    else:
        full_prompt = resolve_context(sender, incoming_msg)
        user_context[sender] = {"last_prompt": full_prompt}  # store for رزرو
        reply = await get_gpt_response(full_prompt)

    # Send reply
    try:
        requests.post(
            f"https://api.ultramsg.com/{os.getenv('ULTRA_INSTANCE_ID')}/messages/chat",
            data={
                "token": os.getenv("ULTRA_TOKEN"),
                "to": sender,
                "body": reply
            }
        )
    except Exception as e:
        print("🚨 Failed to send message:", e)

    # Log to Google Sheets
    try:
        log_to_sheet(sender, incoming_msg, context=reply)
    except Exception as e:
        print("❌ Failed to log:", e)

    return PlainTextResponse("OK", status_code=200)

# ─────── GPT HANDLER ───────
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

        # Step 2: Scrape data
        if "flight" in request_type:
            data = scrape_flights_playwright()
        elif "hotel" in request_type:
            data = scrape_hotels_playwright()
        else:
            data = scrape_tours_playwright()

        formatted = "\n".join(data) if isinstance(data, list) else str(data)

        # Step 3: Generate GPT reply
        final_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "شما یک دستیار حرفه‌ای گردشگری هستید که به زبان فارسی به سوالات تور، هتل و پرواز پاسخ می‌دهد."},
                {"role": "user", "content": f"{prompt}\n\nاطلاعات:\n{formatted}"}
            ],
            temperature=0.7
        )
        return final_response.choices[0].message["content"].strip()
    except Exception as e:
        print("❌ GPT error:", e)
        return "ببخشید پرنسس.. الان نمی‌تونم جواب بدم."
