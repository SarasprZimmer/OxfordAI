import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def log_user_to_sheet(phone, name, request_type, destination, booking_intent):
    print("🔄 Step 1: Setting up scope and creds...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("gcreds.json", scope)

    print("🔄 Step 2: Authorizing...")
    client = gspread.authorize(creds)

    print("🔄 Step 3: Opening the sheet...")
    sheet = client.open("OxfordAI Leads").sheet1

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("📤 Step 4: Appending the row...")
    sheet.append_row([now, phone, name, request_type, destination, booking_intent], value_input_option="RAW")
    print("✅ Row added!")
