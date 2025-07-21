import sys
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import schedule
import os
from dotenv import load_dotenv
load_dotenv()

target_date = "2025-08-20"  # or dynamically compute next desired date
target_hour = 17 # Must be in 24-hour format (e.g. 19 for 7PM)
target_loc = 12
# MCCarren = 11
# Central Park = 12

def click_first_available_slot_at_7pm(browser, target_date, num_courts=6):
    target_row = target_hour - 5
    xpath_prefix = f"//*[@id='{target_date}']/table/tbody/tr[{target_row}]/td" # row 14 is for 7pm
    
    for col in range(2, num_courts+2):
        try:
            full_xpath = f"{xpath_prefix}[{col}]/a"
            reserve_button = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.XPATH, full_xpath))
            )
            print(f"Found available court in column {col}. Clicking...")
            reserve_button.click()

            # Wait for navigation and click "Confirm and Enter Player Details"
            continue_button_xpath = '//*[@id="no_account"]/div/input'
            continue_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, continue_button_xpath))
            )
            continue_button.click()
            print("Clicked 'Confirm and Enter Player Details'")
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
            print(f"Column {col} failed: {e}")
            browser.save_screenshot(f'error_column_{col}.png')
            continue

    print("No available courts at 7 PM")
    return False

# def fill_out_player_details_mc_carren(browser):
  # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='single_play_exist_2']"))).click() # click this option
  # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='name']"))).send_keys(os.environ.get("full-name"))
  # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='email']"))).send_keys(os.environ.get("email"))
  # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='address']"))).send_keys(os.environ.get("address-line-one")) 
  # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='city']"))).send_keys(os.environ.get("city"))
  # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='zip']"))).send_keys(os.environ.get("postcode"))
  # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='phone']"))).send_keys(os.environ.get("phone-number"))

def fill_out_player_details_mc_carren(browser):
  WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='single_play_exist_2']"))).click() # click this option
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "name"))).send_keys(os.environ.get("full-name"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "email"))).send_keys(os.environ.get("email"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "address"))).send_keys(os.environ.get("address-line-one"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "city"))).send_keys(os.environ.get("city"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "zip"))).send_keys(os.environ.get("postcode"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "phone"))).send_keys(os.environ.get("phone-number"))

# def fill_out_player_details_central_park(browser):
#   WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='permit-number1']"))).send_keys(os.environ.get("permit-number"))
#   WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='name1']"))).send_keys(os.environ.get("full-name"))
#   WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='email']"))).send_keys(os.environ.get("email"))
#   WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='address']"))).send_keys(os.environ.get("address-line-one")) 
#   WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='city']"))).send_keys(os.environ.get("city"))
#   WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='zip']"))).send_keys(os.environ.get("postcode"))
#   WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='phone']"))).send_keys(os.environ.get("phone-number"))

def fill_out_player_details_central_park(browser):
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "permit-number1"))).send_keys(os.environ.get("permit-number"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "name1"))).send_keys(os.environ.get("full-name"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "email"))).send_keys(os.environ.get("email"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "address"))).send_keys(os.environ.get("address-line-one"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "city"))).send_keys(os.environ.get("city"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "zip"))).send_keys(os.environ.get("postcode"))
  WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, "phone"))).send_keys(os.environ.get("phone-number"))

def click_continue_to_payment_button(browser):
  try:
    WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='form_with_validation']/input[2]"))).click()
    return True
  except Exception as e:
    print(f"Error clicking continue to payment: {e}")
    browser.save_screenshot('error_payment.png')
    return False
  
def fill_out_payment_details(browser):
  WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='cc_number']"))).send_keys(os.environ.get("card-number"))
  WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='expdate_month']"))).send_keys(os.environ.get("expiry-month"))
  WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='expdate_year']"))).send_keys(os.environ.get("expiry-year"))
  WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='cvv2_number']"))).send_keys(os.environ.get("cvv"))

def click_pay_now_button(browser):
  WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='btn_pay_cc']"))).click()

def attempt_court_booking(target_date, target_loc):
    print(0)
    # service = Service(ChromeDriverManager().install())
    service = Service('./chromedriver')
    print(1)
    browser = webdriver.Chrome(service=service)
    print(2)
    browser.get(f"https://www.nycgovparks.org/tennisreservation/availability/{target_loc}#{target_date}")
    print(3)
    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, target_date))
    )
    print(4)
    browser.execute_script("arguments[0].scrollIntoView(true);", element)

    num_courts = 6 if target_loc == 12 else 2
    court_available = click_first_available_slot_at_7pm(browser, target_date, num_courts)

    if court_available:
        if target_loc == 12: # CP
           fill_out_player_details_central_park(browser)
        elif target_loc == 11: # McCarren
          fill_out_player_details_mc_carren(browser)
          
        click_continue_to_payment_button(browser)
        fill_out_payment_details(browser)
        click_pay_now_button(browser)

    else:
        return
  

def book_court():
  try:
    print("job running")
    attempt_court_booking(target_date, target_loc)
  except Exception as ex:
    # add proper error handling
    print(ex)
    sys.exit(0)

def schedule_job():
  schedule.every().day.at("18:56").do(book_court)
  while True:
    schedule.run_pending()
    time.sleep(1)

book_court()
# schedule_job()
