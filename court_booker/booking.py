"""
Core Selenium booking logic for NYC Parks tennis courts.

This module drives the browser through every step of the reservation flow:
slot selection → player details → payment → confirmation.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from court_booker.config import (
    CHROMEDRIVER_PATH,
    PERMIT_FIELD,
    PERSONAL_FIELDS,
    RESERVATION_BASE_URL,
    SCREENSHOTS_DIR,
    env,
    get_location,
)

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _screenshot(browser: WebDriver, name: str) -> None:
    """Save a screenshot to the screenshots directory."""
    path = SCREENSHOTS_DIR / f"{name}.png"
    browser.save_screenshot(str(path))


# ── Slot selection ───────────────────────────────────────────────────────────


def _activate_date_tab(browser: WebDriver, target_date: str) -> None:
    """Click the calendar tab for *target_date* so its courts become visible."""
    tab_xpath = f"//a[@href='#{target_date}' and @data-toggle='tab']"
    tab = WebDriverWait(browser, 15).until(
        EC.element_to_be_clickable((By.XPATH, tab_xpath))
    )
    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
    tab.click()
    WebDriverWait(browser, 15).until(
        EC.visibility_of_element_located((By.ID, target_date))
    )
    logger.info("Activated tab for %s", target_date)


def _click_first_available_slot(
    browser: WebDriver,
    target_date: str,
    target_hour: int,
    target_loc: int,
    num_courts: int,
) -> bool:
    """
    Try each court column at the given hour/date and book the first available.

    Returns True if a slot was reserved (player-details page is now showing),
    False if nothing was available.
    """
    target_row = target_hour - 5
    xpath_prefix = f"//*[@id='{target_date}']/table/tbody/tr[{target_row}]/td"

    for col in range(2, num_courts + 2):
        try:
            _screenshot(browser, f"column_{col}_debug")

            full_xpath = f"{xpath_prefix}[{col}]/a"
            elements = browser.find_elements(By.XPATH, full_xpath)
            if not elements:
                logger.debug("No element found at %s", full_xpath)
                continue

            reserve_button = WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.XPATH, full_xpath))
            )
            browser.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", reserve_button
            )
            time.sleep(0.3)

            logger.info("Found element in column %d, clicking…", col)
            reserve_button.click()

            # Wait for the confirmation interstitial and proceed
            continue_button_xpath = '//*[@id="no_account"]/div/input'
            WebDriverWait(browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, continue_button_xpath))
            ).click()
            logger.info("Clicked 'Confirm and Enter Player Details'")

            # Wait for the appropriate form to load
            if target_loc == 12:
                WebDriverWait(browser, 15).until(
                    EC.presence_of_element_located((By.ID, "permit-number1"))
                )
            elif target_loc == 11:
                WebDriverWait(browser, 15).until(
                    EC.presence_of_element_located((By.ID, "single_play_exist_2"))
                )

            return True

        except Exception as e:
            logger.warning("Column %d failed: %s", col, e)
            _screenshot(browser, f"error_column_{col}")
            continue

    logger.info("No available courts at target time")
    return False


# ── Player-details forms ─────────────────────────────────────────────────────

# Mapping of form field IDs for each court "family".
_FIELD_MAP_DEFAULT: dict[str, str] = {
    "full-name": "name",
    "email": "email",
    "address-line-one": "address",
    "city": "city",
    "postcode": "zip",
    "phone-number": "phone",
}

_FIELD_MAP_CENTRAL_PARK: dict[str, str] = {
    "full-name": "name1",
    "email": "email",
    "address-line-one": "address",
    "city": "city",
    "postcode": "zip",
    "phone-number": "phone",
}


def _fill_player_details(browser: WebDriver, is_central_park: bool) -> None:
    """
    Fill in the player reservation form.

    Central Park has a slightly different form (permit number + different name
    field ID) so we branch on *is_central_park*.
    """
    if is_central_park:
        # Central Park requires a permit number first
        logger.info("Filling permit number…")
        WebDriverWait(browser, 15).until(
            EC.visibility_of_element_located((By.ID, "permit-number1"))
        ).send_keys(env(PERMIT_FIELD))
        field_map = _FIELD_MAP_CENTRAL_PARK
    else:
        # Non-CP locations need the "existing single play" radio button
        WebDriverWait(browser, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='single_play_exist_2']"))
        ).click()
        field_map = _FIELD_MAP_DEFAULT

    for env_key, element_id in field_map.items():
        logger.info("Filling %s…", env_key)
        WebDriverWait(browser, 5).until(
            EC.visibility_of_element_located((By.ID, element_id))
        ).send_keys(env(env_key))

    screenshot_name = (
        "fill_out_player_details_central_park"
        if is_central_park
        else "fill_out_player_details"
    )
    _screenshot(browser, screenshot_name)


def _ensure_two_players_selected(browser: WebDriver) -> None:
    """Ensure the '2 players' option is selected (Central Park only)."""
    try:
        btn = WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='num_players_2']"))
        )
        if not btn.is_selected():
            logger.info("Selecting '2 players' button…")
            btn.click()
        else:
            logger.debug("'2 players' already selected.")
    except Exception as e:
        logger.error("Error selecting '2 players': %s", e)
        _screenshot(browser, "error_selecting_two_players")
        raise


# ── Payment ──────────────────────────────────────────────────────────────────


def _click_continue_to_payment(browser: WebDriver) -> bool:
    """Click the 'Continue to Payment' button. Returns True on success."""
    logger.info("Clicking 'Continue to Payment'")
    try:
        WebDriverWait(browser, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='form_with_validation']/input[2]")
            )
        ).click()
        _screenshot(browser, "success_click_continue_to_payment")
        return True
    except Exception as e:
        logger.error("Error clicking continue to payment: %s", e)
        _screenshot(browser, "error_click_continue_to_payment")
        return False


def _fill_payment_details(browser: WebDriver) -> None:
    """Switch into the payment iframe and fill the credit-card form."""
    logger.info("Filling payment details…")
    try:
        iframe = WebDriverWait(browser, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.fancybox-iframe"))
        )
        logger.info("Payment iframe found, switching context…")
        browser.switch_to.frame(iframe)

        _fields = {
            "cc_number": "card-number",
            "expdate_month": "expiry-month",
            "expdate_year": "expiry-year",
            "cvv2_number": "cvv",
        }
        for element_id, env_key in _fields.items():
            WebDriverWait(browser, 15).until(
                EC.element_to_be_clickable((By.ID, element_id))
            ).send_keys(env(env_key))

        logger.info("Payment form filled")
    except Exception as e:
        logger.error("Error filling payment: %s", e)
        _screenshot(browser, "error_fill_payment")
        raise


def _click_pay_now(browser: WebDriver) -> None:
    """Click the final 'Pay Now' button."""
    WebDriverWait(browser, 15).until(
        EC.element_to_be_clickable((By.ID, "btn_pay_cc"))
    ).click()
    logger.info("Clicked Pay Now")


def _handle_payment_confirmation(browser: WebDriver) -> None:
    """Wait for the payment iframe to close and take a success screenshot."""
    try:
        browser.switch_to.default_content()
        WebDriverWait(browser, 40).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "iframe.fancybox-iframe")
            )
        )
        logger.info("Payment iframe closed — assuming success")
        _screenshot(browser, "success")
        logger.info("Successfully booked!")
    except Exception as e:
        logger.error("Error during payment confirmation: %s", e)
        _screenshot(browser, "payment_confirmation_error")
        raise


# ── Public API ───────────────────────────────────────────────────────────────


def book_court(target_date: str, target_hour: int, target_loc: int) -> bool:
    """
    Open the reservation site and attempt to book a single court.

    Args:
        target_date: Booking date in ``YYYY-MM-DD`` format.
        target_hour: Desired hour in 24-hour format (e.g. 19 → 7 PM).
        target_loc:  Court location ID (see ``court_booker.config``).

    Returns:
        ``True`` if the booking succeeded, ``False`` otherwise.
    """
    location = get_location(target_loc)
    service = Service(str(CHROMEDRIVER_PATH))
    browser = webdriver.Chrome(service=service)

    try:
        url = f"{RESERVATION_BASE_URL}/{target_loc}#{target_date}"
        browser.get(url)

        _activate_date_tab(browser, target_date)

        court_available = _click_first_available_slot(
            browser, target_date, target_hour, target_loc, location.num_courts
        )
        if not court_available:
            return False

        if location.requires_permit:
            _ensure_two_players_selected(browser)

        _fill_player_details(browser, is_central_park=location.requires_permit)
        _click_continue_to_payment(browser)
        _fill_payment_details(browser)
        _click_pay_now(browser)
        _handle_payment_confirmation(browser)

        logger.info("Booking completed successfully.")
        return True

    except Exception as e:
        logger.exception("Exception during booking attempt: %s", e)
        return False

    finally:
        browser.quit()
