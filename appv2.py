from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

target_date = "2025-05-15"  # or dynamically compute next desired date
def attempt_court_booking(url):
  # browser + chrome_options for production version
    # chrome_options = add_chrome_options_for_heroku()
    # browser = webdriver.Chrome(service=Service(os.environ.get("CHROMEDRIVER_PATH")), options=chrome_options)
    # browser for dev env
    service = Service('./chromedriver')
    browser = webdriver.Chrome(service=service)
    browser.get(f"https://www.nycgovparks.org/tennisreservation/availability/12#{target_date}")
    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, target_date))
    )
    browser.execute_script("arguments[0].scrollIntoView(true);", element)

    click_first_available_slot_at_7pm(browser, target_date)

    if is_court_confirmed(browser):
        confirm_payment(browser)
    else:
        return
  
def click_first_available_slot_at_7pm(browser, target_date):
    xpath_prefix = f"//*[@id='{target_date}']/table/tbody/tr[14]/td"
    
    # Loop through court columns 2 to 7 (inclusive)
    for col in range(2, 8):
        try:
            full_xpath = f"{xpath_prefix}[{col}]/a"
            reserve_button = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.XPATH, full_xpath))
            )
            print(f"Found available court in column {col}. Clicking...")
            reserve_button.click()
            return True  # Stop after clicking the first available
        except (TimeoutException, NoSuchElementException):
            print(f"No available court in column {col}")
            continue

    print("No available courts at 7 PM")
    return False

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def click_first_available_slot_at_7pm(browser, target_date):
    xpath_prefix = f"//*[@id='{target_date}']/table/tbody/tr[14]/td"
    
    for col in range(2, 8):
        try:
            full_xpath = f"{xpath_prefix}[{col}]/a"
            reserve_button = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.XPATH, full_xpath))
            )
            print(f"Found available court in column {col}. Clicking...")
            reserve_button.click()

            # Wait for navigation and click "Continue without account"
            continue_button_xpath = '//*[@id="no_account"]/div/input'
            continue_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, continue_button_xpath))
            )
            continue_button.click()
            print("Clicked 'Confirm and Enter Player Details'")

            return True
        except Exception as e:
            print(f"Column {col} failed: {e}")
            continue

    print("No available courts at 7 PM")
    return False
