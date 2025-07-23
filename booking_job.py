import schedule
import time
from datetime import datetime, timedelta
from app import book_court

def booking_job():
    today = datetime.today().date()
    primary_date = today + timedelta(days=6)
    saturday_date = today + timedelta(days=29)

    print(f"Running weekly booking job for {primary_date} and {saturday_date}")

    # Try booking 1 → 2 → 3
    booking_attempts = [
        {"target_loc": 13, "target_hour": 20}, # Sutton East Clay courts
        {"target_loc": 2,  "target_hour": 19}, # Riverside Park (119 Street)
    ]

    for attempt in booking_attempts:
        success = book_court(
            target_date=primary_date.strftime("%Y-%m-%d"),
            target_hour=attempt["target_hour"],
            target_loc=attempt["target_loc"]
        )
        if success:
            print(f"Successfully booked {attempt}")
            break
        else:
            print(f"Failed to book {attempt}, trying next...")

    # Always try booking Central Park on Saturdays
    if saturday_date.weekday() == 5:  # 5 = Saturday
        sat_date_str = saturday_date.strftime("%Y-%m-%d")
        print(f"Attempting Saturday slot on {sat_date_str}")
        
        # First try 16:00
        success = book_court(target_date=sat_date_str, target_hour=16, target_loc=12)
        if not success:
            print("16:00 booking failed. Trying 11:00")
            book_court(target_date=sat_date_str, target_hour=11, target_loc=12)

# Schedule to run every Tuesday at 00:00 (i.e., Monday midnight)
schedule.every().tuesday.at("00:00").do(booking_job)

print("Scheduler is running...")
while True:
    schedule.run_pending()
    time.sleep(1)
