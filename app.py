"""
NYC Tennis Court Auto-Booking Script

Automates the process of booking tennis courts through NYC Parks' reservation system.
Includes location-specific flows, payment form handling, and optional multi-court logic.

Environment variables expected (loaded via .env):
- full-name
- email
- address-line-one
- city
- postcode
- phone-number
- permit-number (for Central Park)
- card-number
- expiry-month
- expiry-year
- cvv
"""

# import sys
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# target_date = "2025-08-22"  # or dynamically compute next desired date
# target_hour = 19 # Must be in 24-hour format (e.g. 19 for 7PM)
# target_loc = 12

# Configure the logging system
logging.basicConfig(
    filename="court_booking.log",  # Use None for console-only, or use "court_booking.log"
    level=logging.INFO,  # Set to DEBUG for more verbosity
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def click_first_available_slot_at_(
    browser, target_date, target_hour, target_loc, num_courts=6
):
    """
    Attempts to book the first available court slot at the given hour and date.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.
        target_date (str): The booking date in YYYY-MM-DD format.
        target_hour (int): The desired hour in 24-hour format.
        num_courts (int): Number of courts available at the location.

    Returns:
        bool: True if a slot was successfully booked, False otherwise.
    """
    target_row = target_hour - 5
    xpath_prefix = (
        f"//*[@id='{target_date}']/table/tbody/tr[{target_row}]/td"  # row 14 is for 7pm
    )

    for col in range(2, num_courts + 2):
        try:
            browser.save_screenshot(f"column_{col}_debug.png")

            full_xpath = f"{xpath_prefix}[{col}]/a"
            # Instead of going straight to element_to_be_clickable, test presence and debug:
            elements = browser.find_elements(By.XPATH, full_xpath)
            if not elements:
                logger.debug(f"No element found at {full_xpath}")
                continue
            reserve_button = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.XPATH, full_xpath))
            )

            browser.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", reserve_button
            )
            time.sleep(0.3)  # brief pause to stabilize layout

            logger.info(f"Found element in column {col}, trying to click...")

            # Minimal diagnostic for debugging
            # logger.debug("Checking visibility and display of the element...")
            # is_displayed = reserve_button.is_displayed()
            # is_enabled = reserve_button.is_enabled()
            # logger.debug(f"Displayed: {is_displayed}, Enabled: {is_enabled}")

            reserve_button.click()

            # Wait for navigation and click "Confirm and Enter Player Details"
            continue_button_xpath = '//*[@id="no_account"]/div/input'
            continue_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, continue_button_xpath))
            )
            continue_button.click()
            logger.info("Clicked 'Confirm and Enter Player Details'")
            if target_loc == 12:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.ID, "permit-number1"))
                )
            elif target_loc == 11:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.ID, "single_play_exist_2"))
                )

            return True
        except Exception as e:
            logger.warning(f"Column {col} failed: {e}")
            browser.save_screenshot(f"error_column_{col}.png")
            continue

    logger.info("No available courts at target time")
    return False


def fill_out_player_details(browser):
    """
    Fills out the player reservation form for McCarren, Sutton East, or Riverside Park (119 Street) courts.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.

    Raises:
        EnvironmentError: If any required environment variable is missing.
    """
    required_env_vars = [
        "full-name",
        "email",
        "address-line-one",
        "city",
        "postcode",
        "phone-number",
    ]

    for var in required_env_vars:
        if not os.environ.get(var):
            raise EnvironmentError(f"Missing environment variable: {var}")

    WebDriverWait(browser, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='single_play_exist_2']"))
    ).click()  # click this option
    logger.info("Filling player name...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "name"))
    ).send_keys(os.environ.get("full-name"))
    logger.info("Filling email...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "email"))
    ).send_keys(os.environ.get("email"))
    logger.info("Filling address...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "address"))
    ).send_keys(os.environ.get("address-line-one"))
    logger.info("Filling city...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "city"))
    ).send_keys(os.environ.get("city"))
    logger.info("Filling zip...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "zip"))
    ).send_keys(os.environ.get("postcode"))
    logger.info("Filling phone...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "phone"))
    ).send_keys(os.environ.get("phone-number"))
    browser.save_screenshot("fill_out_player_details.png")


def fill_out_player_details_central_park(browser):
    """
    Fills out the Central Park-specific player reservation form.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.

    Raises:
        EnvironmentError: If any required environment variable is missing.
    """
    required_env_vars = [
        "permit-number",
        "full-name",
        "email",
        "address-line-one",
        "city",
        "postcode",
        "phone-number",
    ]

    for var in required_env_vars:
        if not os.environ.get(var):
            raise EnvironmentError(f"Missing environment variable: {var}")

    logger.info("Filling permit-number...")
    WebDriverWait(browser, 15).until(
        EC.visibility_of_element_located((By.ID, "permit-number1"))
    ).send_keys(os.environ.get("permit-number"))
    logger.info("Filling player name...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "name1"))
    ).send_keys(os.environ.get("full-name"))
    logger.info("Filling email...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "email"))
    ).send_keys(os.environ.get("email"))
    logger.info("Filling address...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "address"))
    ).send_keys(os.environ.get("address-line-one"))
    logger.info("Filling city...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "city"))
    ).send_keys(os.environ.get("city"))
    logger.info("Filling zip...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "zip"))
    ).send_keys(os.environ.get("postcode"))
    logger.info("Filling phone...")
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "phone"))
    ).send_keys(os.environ.get("phone-number"))
    browser.save_screenshot("fill_out_player_details_central_park.png")


def ensure_two_players_selected(browser):
    """
    Ensures that the '2 players' option is selected in the reservation form.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.

    Raises:
        Exception: If the option is not found or not interactable.
    """
    try:
        two_players_button = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='num_players_2']"))
        )
        if not two_players_button.is_selected():
            logger.info("Selecting '2 players' button...")
            two_players_button.click()
        else:
            logger.debug("'2 players' already selected.")
    except Exception as e:
        logger.error(f"Error checking/clicking '2 players' button: {e}")
        browser.save_screenshot("error_selecting_two_players.png")
        raise


def click_continue_to_payment_button(browser):
    """
    Clicks the 'Continue to Payment' button after filling out the reservation form.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.

    Returns:
        bool: True if the button click was successful, False otherwise.
    """
    logger.info("Clicking 'Continue to Payment'")
    try:
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='form_with_validation']/input[2]")
            )
        ).click()
        browser.save_screenshot("success_click_continue_to_payment_button.png")
        return True
    except Exception as e:
        logger.error(f"Error clicking continue to payment: {e}")
        browser.save_screenshot("error_click_continue_to_payment_button.png")


def fill_out_payment_details(browser):
    """
    Fills out the credit card payment form inside the payment iframe.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.

    Raises:
        Exception: If any field is not found or not interactable.
    """
    logger.info("Starting to fill payment details")
    try:
        # Wait for the iframe to appear
        iframe = WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.fancybox-iframe"))
        )
        logger.info("Iframe found, switching context...")
        browser.switch_to.frame(iframe)
        logger.info("Payment form visible")
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='cc_number']"))
        ).send_keys(os.environ.get("card-number"))
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='expdate_month']"))
        ).send_keys(os.environ.get("expiry-month"))
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='expdate_year']"))
        ).send_keys(os.environ.get("expiry-year"))
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='cvv2_number']"))
        ).send_keys(os.environ.get("cvv"))
        logger.info("Payment form filled")
    except Exception as e:
        logger.error(f"Error filling payment: {e}")


def click_pay_now_button(browser):
    """
    Clicks the final 'Pay Now' button to submit the payment.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.
    """
    WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.ID, "btn_pay_cc"))
    ).click()
    logger.info("Clicked Pay Now")


def activate_tab(browser, target_date):
    """
    Activates the calendar tab for the specified date, ensuring its courts are visible.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.
        target_date (str): The booking date in YYYY-MM-DD format.
    """
    tab_xpath = f"//a[@href='#{target_date}' and @data-toggle='tab']"
    tab = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, tab_xpath))
    )
    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
    tab.click()
    WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.ID, target_date))
    )
    logger.info(f"Activated tab for {target_date}")


def handle_payment_confirmation(browser):
    """
    Handles post-payment confirmation steps, such as detecting iframe closure
    and optionally the confirmation page.

    Args:
        browser (webdriver.Chrome): The active Selenium browser session.
    """
    try:
        # Exit the payment iframe (if still inside)
        browser.switch_to.default_content()

        # Wait for the iframe to disappear (Fancybox closes)
        WebDriverWait(browser, 30).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "iframe.fancybox-iframe")
            )
        )
        logger.info("Payment iframe closed, assuming success")

        # Optionally, wait for final confirmation URL
        # try:
        #     WebDriverWait(browser, 15).until(
        #         EC.url_contains("/tennisreservation/thankyou")
        #     )
        #     print("Payment completed successfully.")
        # except:
        #     print("Warning: Confirmation page not detected. Manual check may be required.")

        # Screenshot confirmation
        browser.save_screenshot("success.png")
        logger.info("Successfully booked!")

    except Exception as e:
        logger.error(f"Error during payment confirmation: {e}")
        browser.save_screenshot("payment_confirmation_error.png")


def attempt_court_booking(target_date, target_hour, target_loc):
    """
    Opens the reservation site and attempts to book a court based on input parameters.

    Args:
        target_date (str): The booking date in YYYY-MM-DD format.
        target_hour (int): Desired hour in 24-hour format (e.g., 19 for 7 PM).
        target_loc (int): Court location ID.

    Returns:
        None
    """
    service = Service("./chromedriver")
    browser = webdriver.Chrome(service=service)
    browser.get(
        f"https://www.nycgovparks.org/tennisreservation/availability/{target_loc}#{target_date}"
    )

    activate_tab(browser, target_date)

    num_courts = 6 if target_loc == 12 else 2
    court_available = click_first_available_slot_at_(
        browser, target_date, target_hour, target_loc, num_courts
    )

    if court_available:
        if target_loc == 12:  # CP
            ensure_two_players_selected(browser)
            fill_out_player_details_central_park(browser)
        else:  # McCarren, Sutton East or Riverside 119st
            fill_out_player_details(browser)

        click_continue_to_payment_button(browser)
        fill_out_payment_details(browser)
        click_pay_now_button(browser)

        # Handle post-payment confirmation and success
        handle_payment_confirmation(browser)

    else:
        return


def book_court(target_date, target_hour, target_loc):
    """
    Entry point wrapper that attempts a court booking and handles errors.

    Args:
        target_date (str): The booking date in YYYY-MM-DD format.
        target_hour (int): Desired hour in 24-hour format.
        target_loc (int): Court location ID.

    Returns:
        bool: True if booking succeeded, False otherwise.
    """
    try:
        attempt_court_booking(target_date, target_hour, target_loc)
        return True
    except Exception as ex:
        logger.exception(f"Booking failed: {ex}")
        # sys.exit(0)
        return False


# book_court()
