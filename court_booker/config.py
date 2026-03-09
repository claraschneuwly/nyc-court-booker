"""
Centralised configuration, constants, and environment loading.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
JOBS_CONFIG_PATH = ROOT_DIR / "jobs.yaml"
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"
CHROMEDRIVER_PATH = ROOT_DIR / "chromedriver"

# Ensure the screenshots directory exists at import time
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Environment
load_dotenv(ROOT_DIR / ".env")

# Booking URL
RESERVATION_BASE_URL = (
    "https://www.nycgovparks.org/tennisreservation/availability"
)

# Court locations
@dataclass(frozen=True)
class Location:
    """Immutable metadata for a tennis-court location."""

    id: int
    name: str
    num_courts: int
    requires_permit: bool = False


CENTRAL_PARK = Location(id=12, name="Central Park", num_courts=6, requires_permit=True)
SUTTON_EAST = Location(id=13, name="Sutton East", num_courts=2)
RIVERSIDE_119 = Location(id=2, name="Riverside Park (119 St)", num_courts=2)
MCCARREN = Location(id=11, name="McCarren", num_courts=2)

LOCATIONS: dict[int, Location] = {
    loc.id: loc for loc in (CENTRAL_PARK, SUTTON_EAST, RIVERSIDE_119, MCCARREN)
}

LOCATION_NAMES: dict[int, str] = {loc_id: loc.name for loc_id, loc in LOCATIONS.items()}


def get_location(location_id: int) -> Location:
    """Return the Location for *location_id*, or a sensible default."""
    return LOCATIONS.get(
        location_id,
        Location(id=location_id, name=f"Location {location_id}", num_courts=2),
    )


# User and payment information
PERSONAL_FIELDS = [
    "full-name",
    "email",
    "address-line-one",
    "city",
    "postcode",
    "phone-number",
]

PAYMENT_FIELDS = [
    "card-number",
    "expiry-month",
    "expiry-year",
    "cvv",
]

PERMIT_FIELD = "permit-number"


def env(key: str) -> str:
    """Return an environment variable or raise with a clear message."""
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value


# Telegram notification configuration

TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")
