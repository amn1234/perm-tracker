import os
import smtplib
from datetime import datetime
import zoneinfo
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

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

def check_via_headless_browser():
    try:
        # 1. Evaluate explicit Eastern Time zone window
        est_zone = zoneinfo.ZoneInfo("America/New_York")
        today_est = datetime.now(est_zone)
        
        try:
            today_str = today_est.strftime("%-m/%-d/%Y")
        except ValueError:
            today_str = f"{today_est.month}/{today_est.day}/{today_est.year}"
            
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

        # 3. Pull directly using an automated browser instance
        print("Launching headless Chromium instance...")
        scraped_date = "Old Date / Not Updated"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print(f"Navigating to {DATA_URL} and waiting for text layout hydration...")
            page.goto(DATA_URL, wait_until="networkidle")
            
            # Extract the raw rendered layout text contents from the body tag
            fully_rendered_text = page.locator("body").inner_text()
            browser.close()

        # 4. Perform dynamic data verification
        if today_str in fully_rendered_text:
            scraped_date = today_str
            print(f"🎯 Match Confirmed! Today's date '{today_str}' discovered inside the fully hydrated layout runtime.")
        else:
            print(f"ℹ️ Today's target date '{today_str}' is still missing from the active layout context.")

        # 5. Core Validation Logic
        if scraped_date == today_str:
            send_email(scraped_date)
            with open(LAST_DATE_FILE, "w") as f:
                f.write(scraped_date)
            print(f"Success! State saved to {LAST_DATE_FILE}. No more alerts will send today.")
        else:
            print(f"Dashboard has not updated to today's date yet. Pipeline will re-check in 5 minutes.")

    except Exception as e:
        print(f"Check execution failure details: {e}")

if __name__ == "__main__":
    check_via_headless_browser()
