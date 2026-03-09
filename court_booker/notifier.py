"""
Telegram notification module.

Sends push notifications to your phone via a Telegram bot.
All API calls are wrapped so a Telegram outage can never interfere with an
actual booking attempt.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from court_booker.config import LOCATION_NAMES, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _format_hour(hour: int) -> str:
    """Convert a 24-hour integer to a readable string, e.g. 20 → '8:00 PM'."""
    period = "AM" if hour < 12 else "PM"
    display = hour if hour <= 12 else hour - 12
    if display == 0:
        display = 12
    return f"{display}:00 {period}"


def send_telegram(message: str) -> bool:
    """
    Post *message* via the Telegram Bot API.

    Returns ``True`` on success, ``False`` on any error.
    Never raises — a Telegram failure must not crash a booking run.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning(
            "Telegram not configured (missing TELEGRAM_BOT_TOKEN or "
            "TELEGRAM_CHAT_ID). Skipping notification."
        )
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }
    ).encode("utf-8")

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
            logger.warning("Telegram API returned status %d", resp.status)
            return False
    except urllib.error.URLError as exc:
        logger.warning("Telegram notification failed: %s", exc)
        return False
    except Exception as exc:
        logger.warning("Unexpected error sending Telegram notification: %s", exc)
        return False


# ── Convenience helpers ──────────────────────────────────────────────────────


def notify_booking_success(
    job_name: str, location: int, hour: int, date_str: str
) -> None:
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


def notify_booking_failure(
    job_name: str, num_attempts: int, date_str: str
) -> None:
    """Notify that all booking attempts for a job failed."""
    msg = (
        f"❌ <b>Booking failed</b>\n"
        f"All {num_attempts} attempt(s) failed for {date_str}\n"
        f"🏷 Job: {job_name}"
    )
    send_telegram(msg)


def notify_bot_error(job_name: str, error: Exception) -> None:
    """Notify that the bot crashed with an unexpected error."""
    error_summary = str(error)[:300]
    msg = (
        f"⚠️ <b>Bot error</b>\n"
        f"Job <code>{job_name}</code> crashed:\n"
        f"<pre>{error_summary}</pre>"
    )
    send_telegram(msg)
