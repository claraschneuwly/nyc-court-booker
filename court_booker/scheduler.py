"""
Job runner for cron-based court bookings.

All job definitions (locations, hours, days offset, cron schedules) are loaded
from ``jobs.yaml``.  Each cron entry calls the CLI entry-point with a job name:

    python -m court_booker <job_name>

The runner looks up that job in ``jobs.yaml`` and executes the booking attempts
in order, stopping at the first success.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta

import yaml

from court_booker.booking import book_court
from court_booker.config import JOBS_CONFIG_PATH
from court_booker.notifier import (
    notify_booking_failure,
    notify_booking_success,
    notify_bot_error,
)

logger = logging.getLogger(__name__)


def load_jobs() -> dict:
    """Load and validate ``jobs.yaml``, returning the jobs dict."""
    if not JOBS_CONFIG_PATH.exists():
        logger.error("Config file not found: %s", JOBS_CONFIG_PATH)
        print(f"Error: Config file not found: {JOBS_CONFIG_PATH}")
        sys.exit(2)

    with open(JOBS_CONFIG_PATH, "r") as fh:
        config = yaml.safe_load(fh)

    if not config or "jobs" not in config:
        logger.error("Config file is empty or missing 'jobs' key.")
        print("Error: jobs.yaml must contain a 'jobs' key.")
        sys.exit(2)

    return config["jobs"]


def run_job(job_name: str, job_config: dict) -> bool:
    """
    Execute a single booking job based on its YAML config.

    Tries each attempt in order, returning ``True`` on the first success.
    """
    days_ahead: int = job_config["days_ahead"]
    attempts: list[dict] = job_config["attempts"]

    target_date = datetime.today().date() + timedelta(days=days_ahead)
    date_str = target_date.strftime("%Y-%m-%d")

    logger.info("[%s] Booking for %s (%d days ahead)", job_name, date_str, days_ahead)

    for i, attempt in enumerate(attempts, 1):
        location: int = attempt["location"]
        hour: int = attempt["hour"]

        logger.info(
            "[%s] Attempt %d/%d: location=%d, hour=%d:00, date=%s",
            job_name,
            i,
            len(attempts),
            location,
            hour,
            date_str,
        )

        success = book_court(
            target_date=date_str,
            target_hour=hour,
            target_loc=location,
        )

        if success:
            logger.info(
                "[%s] Successfully booked location=%d at %d:00 on %s",
                job_name,
                location,
                hour,
                date_str,
            )
            notify_booking_success(job_name, location, hour, date_str)
            return True

        logger.warning(
            "[%s] Failed to book location=%d at %d:00 on %s",
            job_name,
            location,
            hour,
            date_str,
        )

    logger.warning("[%s] All %d booking attempt(s) failed.", job_name, len(attempts))
    notify_booking_failure(job_name, len(attempts), date_str)
    return False


def main(argv: list[str] | None = None) -> None:
    """CLI entry-point.  Parses ``argv`` and runs the requested job."""
    from court_booker.logging_config import setup_logging

    setup_logging()

    args = argv if argv is not None else sys.argv[1:]
    jobs = load_jobs()
    valid_jobs = list(jobs.keys())

    if len(args) != 1 or args[0] not in valid_jobs:
        print(f"Usage: python -m court_booker <job_name>")
        print(f"Valid jobs (from jobs.yaml): {', '.join(valid_jobs)}")
        sys.exit(2)

    job_name = args[0]
    job_config = jobs[job_name]

    try:
        logger.info("Starting job: %s", job_name)
        success = run_job(job_name, job_config)
        logger.info("Job '%s' completed. Success: %s", job_name, success)
        sys.exit(0 if success else 1)
    except Exception as exc:
        logger.exception("Job '%s' failed with error: %s", job_name, exc)
        notify_bot_error(job_name, exc)
        sys.exit(1)
