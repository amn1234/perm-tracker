import os
import requests
import smtplib
from datetime import datetime
import zoneinfo
from email.mime.text import MIMEText

# Use the page's direct background data pipeline rather than rendering the UI
DATA_URL = "https://permupdate.com"  # Replace this with your dynamic backend endpoint
LAST_DATE_FILE = "last_known_date.txt"

# Pull secret authentication credentials securely from GitHub environment secrets
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def send_email(current_date):
    print(f"🔄 Dispatched alert routine. Notifying inbox of update: {current_date}")
    
    msg = MIMEText(f"The PERM dashboard date field has been updated to today's date: {current_date}")
    msg["Subject"] = "🎉 PERM Dashboard Updated for Today!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        print("📨 Notification email successfully delivered.")
    except Exception as e:
        print(f"❌ Failed to deliver email: {e}")

def check_via_api():
    try:
        # 1. Force the system timezone evaluation to match the EST window explicitly
        est_zone = zoneinfo.ZoneInfo("America/New_York")
        today_est = datetime.now(est_zone)
        today_str = today_est.strftime("%m/%d/%Y").replace("/0", "/").lstrip("0")
        print(f"System Time Baseline (Today EST): '{today_str}'")

        # 2. Check if we already successfully notified you today
        if os.path.exists(LAST_DATE_FILE):
            with open(LAST_DATE_FILE, "r") as f:
                last_notified_date = f.read().strip()
        else:
            last_notified_date = ""

        if last_notified_date == today_str:
            print(f"Already sent today's alert ({today_str}). Skipping check to prevent double-emailing.")
            return

        # 3. Connect to the data source
        print("Connecting to the page source data layer...")
        response = requests.get(DATA_URL, timeout=10)
        
        try:
            data = response.json()
            scraped_date = data.get("lastSyncDate", "").strip() 
        except Exception:
            print("⚠️ URL returned HTML instead of JSON. Injecting a mock date payload for testing...")
            scraped_date = "9/23/2026"  
        
        print(f"Dashboard Date Found: '{scraped_date}'")

        # 4. Core Validation Logic
        if scraped_date == today_str:
            send_email(scraped_date)
            
            with open(LAST_DATE_FILE, "w") as f:
                f.write(scraped_date)
            print(f"Success! State saved to {LAST_DATE_FILE}. No more alerts will send today.")
        else:
            print(f"Dashboard date ({scraped_date}) is not today's date ({today_str}) yet. Pipeline will re-check in 5 minutes.")

    except Exception as e:
        print(f"API Check execution failure details: {e}")

if __name__ == "__main__":
    check_via_api()
