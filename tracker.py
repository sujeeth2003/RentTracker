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

