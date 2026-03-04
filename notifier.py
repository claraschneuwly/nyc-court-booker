"""
Telegram notification module for NYC Court Booker.

Sends push notifications to your phone via a Telegram bot.
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.
"""

import os
import json
import logging
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Telegram config ──────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── Location ID → human-readable name ───────────────────────────────────────

LOCATION_NAMES = {
    12: "Central Park",
    13: "Sutton East",
    2: "Riverside Park (119 St)",
    11: "McCarren",
}


def _format_hour(hour: int) -> str:
    """Convert 24h integer to readable time, e.g. 20 → '8:00 PM'."""
    period = "AM" if hour < 12 else "PM"
    display = hour if hour <= 12 else hour - 12
    if display == 0:
        display = 12
    return f"{display}:00 {period}"


def send_telegram(message: str) -> bool:
    """
    Send a message via the Telegram Bot API.

    Returns True on success, False on any error.
    Never raises — a Telegram failure must not crash the booking run.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning(
            "Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID). "
            "Skipping notification."
        )
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                logger.info("Telegram notification sent.")
                return True
            else:
                logger.warning(f"Telegram API returned status {resp.status}")
                return False
    except urllib.error.URLError as e:
        logger.warning(f"Telegram notification failed: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error sending Telegram notification: {e}")
        return False


# ── Convenience helpers ──────────────────────────────────────────────────────


def notify_booking_success(job_name: str, location: int, hour: int, date_str: str):
    """Notify that a court was successfully booked."""
    loc_name = LOCATION_NAMES.get(location, f"Location {location}")
    time_str = _format_hour(hour)
    msg = (
        f"✅ <b>Court booked!</b>\n"
        f"📍 {loc_name}\n"
        f"🕐 {time_str} on {date_str}\n"
        f"🏷 Job: {job_name}"
    )
    send_telegram(msg)


def notify_booking_failure(job_name: str, num_attempts: int, date_str: str):
    """Notify that all booking attempts for a job failed (no court available)."""
    msg = (
        f"❌ <b>Booking failed</b>\n"
        f"All {num_attempts} attempt(s) failed for {date_str}\n"
        f"🏷 Job: {job_name}"
    )
    send_telegram(msg)


def notify_bot_error(job_name: str, error: Exception):
    """Notify that the bot crashed with an unexpected error."""
    error_summary = str(error)[:300]  # truncate long tracebacks
    msg = (
        f"⚠️ <b>Bot error</b>\n"
        f"Job <code>{job_name}</code> crashed:\n"
        f"<pre>{error_summary}</pre>"
    )
    send_telegram(msg)
