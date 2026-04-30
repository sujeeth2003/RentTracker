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
