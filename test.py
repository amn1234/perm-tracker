import os
import requests
import smtplib
from datetime import datetime
import zoneinfo
from email.mime.text import MIMEText

# Swapping the base URL out for the direct Next.js API data hydration route channel
DATA_URL = "https://permupdate.com"  # Targets the raw dynamic background metrics collection directly
LAST_DATE_FILE = "last_known_date.txt"

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
        with smtplib.SMTP("://gmail.com", 587) as server:
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

        # 3. Pull directly from the target system database data layer endpoint
        print("Connecting directly to the background API endpoint stream...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(DATA_URL, headers=headers, timeout=10)
        
        # Fallback check path: If the API endpoint path structure is shifted, query the main route array alternative
        if response.status_code != 200:
            print(f"⚠️ Primary API path returned code {response.status_code}. Querying fallback database channel...")
            response = requests.get("https://permupdate.com", headers=headers, timeout=10)

        # Parse the structured JSON database object directly
        data = response.json()
        
        # Extract target property mapping values (handles typical structural permutations)
        scraped_date = data.get("lastSyncDate") or data.get("updatedAt") or data.get("date")
        
        # If deeply nested under a structural collection array, extract from standard record root
        if isinstance(data, list) and len(data) > 0:
            scraped_date = data[0].get("date") or data[0].get("lastSyncDate")

        if not scraped_date:
            print("❌ Unable to pinpoint the date parameter property inside the API payload tree. Response body structure:")
            print(str(data)[:200])
            return
            
        # Clean formatting structure to match target format pattern string profiles cleanly
        scraped_date = scraped_date.split("T")[0].strip() # Strips out timestamps if present
        
        # Convert date to standard M/D/YYYY display format if it returns as YYYY-MM-DD
        if "-" in scraped_date:
            try:
                date_obj = datetime.strptime(scraped_date, "%Y-%m-%d")
                scraped_date = date_obj.strftime("%m/%d/%Y").replace("/0", "/").lstrip("0")
            except ValueError:
                pass

        print(f"Live Dashboard Date Found: '{scraped_date}'")

        # 4. Core Validation Logic
        if scraped_date == today_str:
            send_email(scraped_date)
            with open(LAST_DATE_FILE, "w") as f:
                f.write(scraped_date)
            print(f"Success! State saved to {LAST_DATE_FILE}. No more alerts will send today.")
        else:
            print(f"Dashboard date ({scraped_date}) is not today's date ({today_str}) yet. Pipeline will re-check in 5 minutes.")

    except Exception as e:
        print(f"Check execution failure details: {e}")

if __name__ == "__main__":
    check_via_api()
