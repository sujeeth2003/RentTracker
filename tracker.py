import os

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")


import requests
import json
import smtplib
from email.mime.text import MIMEText

URL = "https://www.liveparksideapartments.com/wp-json/theme/entrata/v1/floor-plans"
THRESHOLD = 700
STATE_FILE = "state.json"


# ------------------ EMAIL ------------------
def send_email_alert(message):
    msg = MIMEText(message)
    msg["Subject"] = "Rent Price Alert"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)


# ------------------ FETCH ------------------
def fetch_data():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    return requests.get(URL, headers=headers).json()


# ------------------ EXTRACT ------------------
def get_lowest_price(data):
    lowest = None
    best_plan = None

    for category, cat_data in data.get("categories", {}).items():
        for plan in cat_data.get("floorplans", []):

            if plan.get("sold_out"):
                continue

            name = plan.get("name")

            for rate in plan.get("rates", []):
                price = rate.get("value")
                special = rate.get("special_value")

                price = int(price) if price else None
                special = int(special) if special else None

                final_price = special if special else price

                if final_price:
                    if lowest is None or final_price < lowest:
                        lowest = final_price
                        best_plan = f"{category} - {name}"

    return lowest, best_plan


# ------------------ STATE ------------------
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"lowest": None}


def save_state(lowest):
    with open(STATE_FILE, "w") as f:
        json.dump({"lowest": lowest}, f)


# ------------------ MAIN ------------------
def main():
    data = fetch_data()
    current_lowest, plan = get_lowest_price(data)

    state = load_state()
    prev_lowest = state.get("lowest")

    print("Current:", current_lowest, "| Previous:", prev_lowest)

    # 🔴 alert condition
    if current_lowest and current_lowest < THRESHOLD:
        if prev_lowest is None or current_lowest < prev_lowest:
            message = f"""
New lowest rent detected!

Plan: {plan}
Price: ${current_lowest}
Previous Lowest: {prev_lowest}
"""
            send_email_alert(message)
            save_state(current_lowest)
        else:
            print("No new lower price")
    else:
        print("Threshold not met")


if __name__ == "__main__":
    main()
