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
