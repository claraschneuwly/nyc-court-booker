"""
Cron-based scheduler for booking NYC Parks tennis courts.

All job definitions (locations, hours, days offset, cron schedules) are loaded
from jobs.yaml. Each cron job calls this script with a job name:

    python weekly_court_scheduler.py <job_name>

The script looks up that job in jobs.yaml and executes the booking attempts
in order, stopping at the first success.

Dependencies:
- PyYAML
- app.py (must contain a `book_court(target_date, target_hour, target_loc)` function)
"""

import os
import sys
import logging
from datetime import datetime, timedelta

import yaml

from app import book_court
from notifier import notify_booking_success, notify_booking_failure, notify_bot_error

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "jobs.yaml")

# Configure logging
logging.basicConfig(
    filename=os.path.join(SCRIPT_DIR, "scheduler.log"),
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config():
    """Load and validate jobs.yaml, returning the jobs dict."""
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"Config file not found: {CONFIG_PATH}")
        print(f"Error: Config file not found: {CONFIG_PATH}")
        sys.exit(2)

    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    if not config or "jobs" not in config:
        logger.error("Config file is empty or missing 'jobs' key.")
        print("Error: jobs.yaml must contain a 'jobs' key.")
        sys.exit(2)

    return config["jobs"]


def run_job(job_name, job_config):
    """
    Execute a single booking job based on its YAML config.

    Args:
        job_name (str): Name of the job (for logging).
        job_config (dict): Job definition with keys: days_ahead, attempts.
    """
    days_ahead = job_config["days_ahead"]
    attempts = job_config["attempts"]

    today = datetime.today().date()
    target_date = today + timedelta(days=days_ahead)
    date_str = target_date.strftime("%Y-%m-%d")

    logger.info(f"[{job_name}] Booking for {date_str} ({days_ahead} days ahead)")

    for i, attempt in enumerate(attempts, 1):
        location = attempt["location"]
        hour = attempt["hour"]

        logger.info(
            f"[{job_name}] Attempt {i}/{len(attempts)}: "
            f"location={location}, hour={hour}:00, date={date_str}"
        )

        success = book_court(
            target_date=date_str,
            target_hour=hour,
            target_loc=location,
        )

        if success:
            logger.info(
                f"[{job_name}] Successfully booked location={location} "
                f"at {hour}:00 on {date_str}"
            )
            notify_booking_success(job_name, location, hour, date_str)
            return True
        else:
            logger.warning(
                f"[{job_name}] Failed to book location={location} "
                f"at {hour}:00 on {date_str}"
            )

    logger.warning(f"[{job_name}] All {len(attempts)} booking attempt(s) failed.")
    notify_booking_failure(job_name, len(attempts), date_str)
    return False


if __name__ == "__main__":
    jobs = load_config()
    valid_jobs = list(jobs.keys())

    if len(sys.argv) != 2 or sys.argv[1] not in valid_jobs:
        print(f"Usage: python {sys.argv[0]} <job_name>")
        print(f"Valid jobs (from jobs.yaml): {', '.join(valid_jobs)}")
        sys.exit(2)

    job_name = sys.argv[1]
    job_config = jobs[job_name]

    try:
        logger.info(f"Starting job: {job_name}")
        success = run_job(job_name, job_config)
        logger.info(f"Job '{job_name}' completed. Success: {success}")
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"Job '{job_name}' failed with error: {e}")
        notify_bot_error(job_name, e)
        sys.exit(1)
