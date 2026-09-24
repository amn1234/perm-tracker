import os
import requests
import smtplib
import json
from datetime import datetime
import zoneinfo
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

DATA_URL = "https://permupdate.com"  
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

        # 3. Fetch and parse web content
        print("Connecting to permupdate.com to parse application script memory...")
        response = requests.get(DATA_URL, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the raw background data script element Next.js relies on
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        scraped_date = None
        if next_data_script:
            # Parse the hidden database text directly
            page_data = json.loads(next_data_script.string)
            
            # Drill into the components tree properties to extract the dashboard date
            # This searches the backend page variables dynamically for the date pattern
            props = page_data.get('props', {}).get('pageProps', {})
            
            # Look for typical Next.js state data placements or search the structure safely
            scraped_date = props.get('lastSyncDate') or props.get('initialState', {}).get('lastSyncDate')
            
            # Fallback text search if keys are deeply nested inside different paths
            if not scraped_date:
                data_str = next_data_script.string
                # Simple extraction fallback if text contains the raw string date
                import re
                date_match = re.search(r'"lastSyncDate":"([^"]+)"', data_str)
                if date_match:
                    scraped_date = date_match.group(1)
        
        # Ultimate fallback: search all string contents on the page layout for standard date formats
        if not scraped_date:
            print("⚠️ Next.js block empty. Running structural text search fallback...")
            all_text = soup.get_text()
            import re
            # Searches the source for any string pattern matching a date (e.g., 9/23/2026)
            found_dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b', all_text)
            if found_dates:
                scraped_date = found_dates[0]

        if not scraped_date:
            print("❌ Unable to extract date from live application layout.")
            return
            
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
