import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

print("SCRIPT STARTED")

# ---------------- CONFIG ----------------
URL = "https://www.liveparksideapartments.com/wp-json/theme/entrata/v1/floor-plans"
THRESHOLD = 700
STATE_FILE = "state.json"

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not EMAIL or not APP_PASSWORD:
    print("Missing EMAIL or APP_PASSWORD environment variables")
    exit(1)

print("Environment variables loaded")


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

        print("Email sent")

    except Exception as e:
        print("Email error:", e)


# ---------------- FETCH ----------------
def fetch_data():
    try:
        print("Fetching API...")

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.liveparksideapartments.com/floor-plans/"
        }

        r = requests.get(URL, headers=headers, timeout=10)
        r.raise_for_status()

        return r.json()

    except Exception as e:
        print("API fetch error:", e)
        return None


# ---------------- SAFE INT ----------------
def safe_int(x):
    try:
        return int(x)
    except:
        return None


# ---------------- EXTRACT ----------------
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

                final_price = special if special is not None else price

                if final_price is not None:
                    if lowest is None or final_price < lowest:
                        lowest = final_price
                        best_plan = f"{category} - {name}"

    return lowest, best_plan


# ---------------- STATE ----------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"lowest_seen": None, "last_alerted": None}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"lowest_seen": None, "last_alerted": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ---------------- MAIN ----------------
def main():
    data = fetch_data()

    if not data:
        print("No data received")
        return

    current_lowest, plan = get_lowest_price(data)

    print(f"Current lowest: {current_lowest} | Plan: {plan}")

    if current_lowest is None:
        print("No valid price found")
        return

    state = load_state()
    lowest_seen = state.get("lowest_seen")
    last_alerted = state.get("last_alerted")

    print(f"Lowest seen: {lowest_seen}")
    print(f"Last alerted: {last_alerted}")

    # update lowest seen
    if lowest_seen is None or current_lowest < lowest_seen:
        lowest_seen = current_lowest

    alert_sent = False

    # alert condition
    if current_lowest < THRESHOLD:
        if last_alerted is None or current_lowest < last_alerted:
            print("New alert triggered")

            message = f"""
Rent Price Alert

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
            print("Already alerted for this price level")
    else:
        print("Price above threshold")

    # save state
    save_state({
        "lowest_seen": lowest_seen,
        "last_alerted": last_alerted
    })

    print("State updated")

    if not alert_sent:
        print("No alert sent this run")


if __name__ == "__main__":
    main()
