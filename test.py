import os
import time
import smtplib
from datetime import datetime, timedelta
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
    
    # Corrected robust multi-port secure mail handshake connection sequence
    try:
        print("📨 Attempting primary secure connection via SMTP TLS (Port 587)...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Enforce TLS transport layer before pushing login info
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        print("📨 Notification email successfully delivered via Port 587.")
    except Exception as e:
        print(f"❌ Primary Port 587 connection failure: {e}. Trying fallback SSL (Port 465)...")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
            print("📨 Notification email successfully delivered via Port 465 SSL fallback.")
        except Exception as fallback_error:
            print(f"❌ Failed to deliver email completely through all server routes: {fallback_error}")

def check_via_headless_browser():
    try:
        # 1. Evaluate explicit Eastern Time zone window
        est_zone = zoneinfo.ZoneInfo("America/New_York")
        today_est = datetime.now(est_zone)
        today_str = f"{today_est.month}/{today_est.day}/{today_est.year}"
            
        print(f"System Time Baseline (Today EST): '{today_str}'")

        # 2. Check if we already successfully notified you today
        if os.path.exists(LAST_DATE_FILE):
            with open(LAST_DATE_FILE, "r") as f:
                last_notified_date = f.read().strip()
        else:
            last_notified_date = ""

        if last_notified_date == today_str:
            print(f"Already sent today's alert ({today_str}). Checking window complete for today.")
            return True  

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
            return True  
        else:
            print(f"Dashboard has not updated to today's date yet. Will re-check in 5 minutes.")
            return False  

    except Exception as e:
        print(f"Check execution failure details: {e}")
        return False

# --- CONTINUOUS MAIN APPLICATION RUNTIME LOOP ---
if __name__ == "__main__":
    est_zone = zoneinfo.ZoneInfo("America/New_York")
    print("🚀 PERM Python Monitoring Service Started Successfully.")
    
    while True:
        now_est = datetime.now(est_zone)
        
        # Condition A: It is past 9:00 PM EST (21:00) and before midnight
        if now_est.hour >= 21:
            print(f"\n⏰ Window open [{now_est.strftime('%I:%M:%S %p')} EST]. Executing update probe...")
            job_finished_for_today = check_via_headless_browser()
            
            if job_finished_for_today:
                # If an alert was sent or cached, calculate sleep until exactly 9:00 PM tomorrow
                tomorrow_target = (now_est + timedelta(days=1)).replace(hour=21, minute=0, second=0, microsecond=0)
                sleep_seconds = int((tomorrow_target - now_est).total_seconds())
                print(f"💤 Alert sequence handled. Sleeping for {sleep_seconds // 3600} hours until tomorrow at 9:00 PM EST.")
                time.sleep(sleep_seconds)
            else:
                # Wait exactly 5 minutes (300 seconds) before executing next web probe
                time.sleep(300)
                
        # Condition B: It is during the daytime (before 9:00 PM)
        else:
            # Calculate exactly how many seconds are left until 9:00 PM today arrives
            today_target = now_est.replace(hour=21, minute=0, second=0, microsecond=0)
            sleep_seconds = int((today_target - now_est).total_seconds())
            print(f"💤 Out of window [{now_est.strftime('%I:%M:%S %p')} EST]. Sleeping until 9:00 PM today ({sleep_seconds // 3600} hours remaining).")
            time.sleep(sleep_seconds)
