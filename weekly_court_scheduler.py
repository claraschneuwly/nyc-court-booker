"""
This script runs a scheduled job every Tuesday at 00:00 AM (midnight Monday into Tuesday)
to automatically book tennis courts through the NYC Parks reservation system.

It attempts booking in the following order:
1. Sutton East (target_loc=13) at 8PM
2. Riverside Park (target_loc=2) at 7PM

Additionally, if the Saturday 29 days from today is indeed a Saturday, it will also try to book
Central Park (target_loc=12) at 4PM, falling back to 11AM if that fails.

Dependencies:
- schedule
- app.py (must contain a `book_court(target_date, target_hour, target_loc)` function)
"""

import schedule
import time
import logging
from datetime import datetime, timedelta
from app import book_court

# Configure logging
logging.basicConfig(
    filename="scheduler.log",  # Log file name
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def booking_job():
    """
    Executes the weekly booking routine.

    - Books courts for the upcoming weekend (6 days ahead) with fallback options.
    - Additionally attempts Central Park booking for a Saturday 29 days in the future.
    """
    today = datetime.today().date()
    primary_date = today + timedelta(days=7)
    saturday_date = today + timedelta(days=29)

    logger.info(
        f"Running weekly booking job for primary_date={primary_date} and saturday_date={saturday_date}"
    )

    # Try booking 1 → 2 → 3
    booking_attempts = [
        {"target_loc": 13, "target_hour": 20},  # Sutton East Clay courts
        # {"target_loc": 2, "target_hour": 19},  # Riverside Park (119 Street)
    ]

    for attempt in booking_attempts:
        logger.info(
            f"Trying booking at loc={attempt['target_loc']} at {attempt['target_hour']}:00 on {primary_date}"
        )
        success = book_court(
            target_date=primary_date.strftime("%Y-%m-%d"),
            target_hour=attempt["target_hour"],
            target_loc=attempt["target_loc"],
        )
        if success:
            logger.info(f"Successfully booked: {attempt}")
            break
        else:
            logger.warning(f"Failed to book: {attempt}")

    # Always try booking Central Park on Saturdays
    if saturday_date.weekday() == 5:  # 5 = Saturday
        sat_date_str = saturday_date.strftime("%Y-%m-%d")
        logger.info(f"Attempting Central Park Saturday slot on {sat_date_str}")

        # First try 16:00
        success = book_court(target_date=sat_date_str, target_hour=16, target_loc=12)
        if not success:
            logger.warning("16:00 booking failed. Trying 11:00")
            book_court(target_date=sat_date_str, target_hour=11, target_loc=12)


# Schedule to run every Tuesday at 00:00 (i.e. Monday night -> Tuesday morning)
schedule.every().tuesday.at("00:00").do(booking_job)

logger.info("Scheduler is running...")
while True:
    schedule.run_pending()
    time.sleep(1)
