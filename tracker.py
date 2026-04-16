import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import json
from google.oauth2.service_account import Credentials
import gspread

print("🚀 SCRIPT STARTED")

# ---------------- CONFIG ----------------
URL = "https://www.liveparksideapartments.com/wp-json/theme/entrata/v1/floor-plans"
THRESHOLD = 700

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

GOOGLE_SHEET_NAME = "Rent Tracker"
GOOGLE_CREDS_FILE = "credentials.json"

if not EMAIL or not APP_PASSWORD:
    print("❌ Missing EMAIL or APP_PASSWORD env variables")
    exit(1)

print("✅ Environment variables loaded")


# ---------------- GOOGLE SHEETS ----------------
def init_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]



    creds_json = json.loads(os.getenv("GOOGLE_CREDS_JSON"))

    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)

    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    return sheet


def log_to_sheet(plan, price, status):
    try:
        sheet = init_sheet()

        sheet.append_row([
            str(datetime.now()),
            plan,
            price,
            status
        ])

        print("📊 Logged to Google Sheets")

    except Exception as e:
        print("❌ Google Sheets logging failed:", e)


# ---------------- EMAIL ----------------
def send_email_alert(message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = "Rent Price Alert"
        msg["From"] = EMAIL
        msg["To"] = EMAIL

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.send_message(msg)

        print("📧 Email sent successfully")

    except Exception as e:
        print("❌ Email failed:", e)


# ---------------- FETCH DATA ----------------
def fetch_data():
    try:
        print("🌐 Fetching API...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.liveparksideapartments.com/floor-plans/",
            "Origin": "https://www.liveparksideapartments.com"
        }

        r = requests.get(URL, headers=headers, timeout=10)
        r.raise_for_status()

        print("✅ API response received")
        return r.json()

    except Exception as e:
        print("❌ API fetch error:", e)
        return None


# ---------------- SAFE INT ----------------
def safe_int(x):
    try:
        return int(x)
    except:
        return None


# ---------------- EXTRACT LOWEST PRICE ----------------
def get_lowest_price(data):
    lowest = None
    best_plan = None

    for category, cat_data in data.get("categories", {}).items():
        for plan in cat_data.get("floorplans", []):

            if plan.get("sold_out"):
                continue

            name = plan.get("name")

            for rate in plan.get("rates", []):
                price = safe_int(rate.get("value"))
                special = safe_int(rate.get("special_value"))

                final_price = special if special else price

                if final_price:
                    if lowest is None or final_price < lowest:
                        lowest = final_price
                        best_plan = f"{category} - {name}"

    return lowest, best_plan


# ---------------- MAIN ----------------
def main():
    data = fetch_data()
    if not data:
        print("❌ No data, exiting")
        return

    current_lowest, plan = get_lowest_price(data)

    print(f"📊 Current lowest: {current_lowest} | Plan: {plan}")

    if current_lowest is None:
        print("❌ No valid price found")
        return

    state_file = "state.json"

    try:
        with open(state_file, "r") as f:
            state = json.load(f)
    except:
        state = {"lowest_seen": None, "last_alerted": None}

    lowest_seen = state.get("lowest_seen")
    last_alerted = state.get("last_alerted")

    print(f"📌 Lowest seen: {lowest_seen}")
    print(f"📌 Last alerted: {last_alerted}")

    if lowest_seen is None or current_lowest < lowest_seen:
        lowest_seen = current_lowest

    alert_sent = False

    if current_lowest < THRESHOLD:
        if last_alerted is None or current_lowest < last_alerted:
            print("🚨 New alert triggered!")

            message = f"""
Rent Price Alert 🚨

Plan: {plan}
Price: ${current_lowest}
Threshold: {THRESHOLD}
Lowest Seen: {lowest_seen}
Time: {datetime.now()}
"""

            send_email_alert(message)
            last_alerted = current_lowest
            alert_sent = True
        else:
            print("ℹ️ Already alerted for this price level")
    else:
        print("ℹ️ Price above threshold")

    # ---------------- LOG TO GOOGLE SHEETS ----------------
    status = "ALERT" if alert_sent else "NORMAL"
    log_to_sheet(plan, current_lowest, status)

    # save state
    with open(state_file, "w") as f:
        json.dump(
            {
                "lowest_seen": lowest_seen,
                "last_alerted": last_alerted,
            },
            f,
        )

    print("💾 State updated")


if __name__ == "__main__":
    main()
