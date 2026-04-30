import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

from google.oauth2.service_account import Credentials
import gspread

print("🚀 SCRIPT STARTED")

# ---------------- CONFIG ----------------
URL = "https://www.liveparksideapartments.com/wp-json/theme/entrata/v1/floor-plans"
THRESHOLD = 700

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

GOOGLE_SHEET_NAME = "Rent Tracker"

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


def get_history_low(sheet):
    """
    Reads all prices from sheet and finds historical lowest price.
    Column format:
    0 timestamp | 1 plan | 2 price | 3 status
    """
    try:
        records = sheet.get_all_values()

        if len(records) <= 1:
            return None  # only header or empty

        prices = []
        for row in records[1:]:
            try:
                prices.append(int(row[2]))
            except:
                continue

        return min(prices) if prices else None

    except Exception as e:
        print("❌ Failed reading sheet history:", e)
        return None


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
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
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
    sheet = init_sheet()

    data = fetch_data()
    if not data:
        print("❌ No data, exiting")
        return

    current_lowest, plan = get_lowest_price(data)

    print(f"📊 Current lowest: {current_lowest} | Plan: {plan}")

    if current_lowest is None:
        print("❌ No valid price found")
        return

    # ---------------- GET HISTORICAL LOW ----------------
    historical_low = get_history_low(sheet)

    print(f"📌 Historical lowest (sheet): {historical_low}")

    alert_sent = False

    # ---------------- ALERT LOGIC ----------------
    if historical_low is None or current_lowest < historical_low:

        if current_lowest < THRESHOLD:
            print("🚨 New ALL-TIME LOW detected!")

            message = f"""
Rent Price Alert 🚨

Plan: {plan}
Price: ${current_lowest}
Threshold: {THRESHOLD}
Previous Lowest (Sheet): {historical_low}
Time: {datetime.now()}
"""

            send_email_alert(message)
            alert_sent = True

    else:
        print("ℹ️ No new lowest price")

    # ---------------- LOG ALWAYS ----------------
    status = "ALERT" if alert_sent else "NORMAL"
    log_to_sheet(plan, current_lowest, status)

    print("💾 Done")


if __name__ == "__main__":
    main()
