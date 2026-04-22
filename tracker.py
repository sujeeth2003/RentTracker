import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

print("🚀 SCRIPT STARTED")

# ---------------- CONFIG ----------------
URL = "https://www.liveparksideapartments.com/wp-json/theme/entrata/v1/floor-plans"
THRESHOLD = 700

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not EMAIL or not APP_PASSWORD:
    print("❌ Missing EMAIL or APP_PASSWORD env variables")
    exit(1)

print("✅ Environment variables loaded")


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
        r = requests.get(URL, timeout=10)
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

    # Load state from GitHub runner (NOT persistent across runs, but OK for logic)
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

    # update lowest seen
    if lowest_seen is None or current_lowest < lowest_seen:
        lowest_seen = current_lowest

    # alert logic
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
        else:
            print("ℹ️ Already alerted for this price level")
    else:
        print("ℹ️ Price above threshold")

    # save state (for same-run tracking only)
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
