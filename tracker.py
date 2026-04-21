import os
import json
import requests
import smtplib
from email.mime.text import MIMEText

URL = "https://www.liveparksideapartments.com/wp-json/theme/entrata/v1/floor-plans"
THRESHOLD = 700

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

STATE_FILE = "state.json"


# ---------------- EMAIL ----------------
def send_email_alert(message):
    msg = MIMEText(message)
    msg["Subject"] = "Rent Price Alert"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)


# ---------------- FETCH ----------------
def fetch_data():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    r = requests.get(URL, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


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

                final_price = special if special else price

                if final_price:
                    if lowest is None or final_price < lowest:
                        lowest = final_price
                        best_plan = f"{category} - {name}"

    return lowest, best_plan


# ---------------- STATE (GitHub-safe) ----------------
def load_state():
    try:
        return json.load(open(STATE_FILE))
    except:
        return {
            "lowest_seen": None,
            "last_alerted": None
        }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ---------------- MAIN ----------------
def main():
    data = fetch_data()
    current_lowest, plan = get_lowest_price(data)

    state = load_state()
    lowest_seen = state.get("lowest_seen")
    last_alerted = state.get("last_alerted")

    print("Current:", current_lowest)
    print("Lowest seen:", lowest_seen)
    print("Last alerted:", last_alerted)

    if current_lowest is None:
        print("No price found")
        return

    # update lowest seen
    if lowest_seen is None or current_lowest < lowest_seen:
        lowest_seen = current_lowest

    # alert condition
    if current_lowest < THRESHOLD:
        if last_alerted is None or current_lowest < last_alerted:
            message = f"""
New rent opportunity detected!

Plan: {plan}
Price: ${current_lowest}
Lowest Seen: {lowest_seen}
Previous Alert: {last_alerted}
"""
            send_email_alert(message)
            last_alerted = current_lowest
        else:
            print("Already alerted for this level")

    # always persist state
    save_state({
        "lowest_seen": lowest_seen,
        "last_alerted": last_alerted
    })


if __name__ == "__main__":
    main()
