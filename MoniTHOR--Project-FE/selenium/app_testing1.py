import datetime
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from utils import get_url_status, certificate_checks

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

url = f"{config['host']}:{config['port']}/"

# Initialize the WebDriver service
def create_driver():
    return webdriver.Chrome()

def is_alert_present(driver):
    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        return True
    except TimeoutException:
        return False

def alert_wait_and_click(driver):
    try:
        if is_alert_present(driver):
            alert = driver.switch_to.alert
            alert.accept()
    except Exception as e:
        print(f"Error handling alert: {e}")

def register(driver, username, password1, password2):
    driver.get(f"{url}/register")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password1").send_keys(password1)
    driver.find_element(By.ID, "password2").send_keys(password2)
    driver.find_element(By.CLASS_NAME, "register-submit").click()
    alert_wait_and_click(driver)

def login(driver, username, password):
    driver.get(f"{url}/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CLASS_NAME, "login-submit").click()

def single_upload(driver, domain):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "single")))
    driver.find_element(By.ID, "single").send_keys(domain)
    driver.find_element(By.CLASS_NAME, "single-submit").click()
    alert_wait_and_click(driver)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "resultsBody")))

def verify_results(driver, domain):
    table_body = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "resultsBody")))
    rows = table_body.find_elements(By.TAG_NAME, "tr")
    
    status, expiration_date, issuer = None, None, None
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells and domain == cells[0].text:
            status = cells[1].text
            expiration_date = cells[2].text
            issuer = cells[3].text
            break

    if not status:
        raise ValueError(f"No results found for domain: {domain}")

    # Validate status
    status_validation = get_url_status(domain)
    if status_validation not in ['OK', 'FAILED']:
        raise ValueError(f"Invalid status: {status_validation}")

    # Validate certificate details
    cert = certificate_checks(domain)
    if expiration_date != cert[0] or issuer != cert[1]:
        raise ValueError(f"Certificate mismatch for domain {domain}")

def perform_user_actions(user_index):
    driver = create_driver()
    try:
        username = f"tester{user_index}"
        password = "tester"

        # Register and login the user
        register(driver, username, password, password)
        login(driver, username, password)

        # Record the start time
        start_time = time.time()

        # Perform single domain upload and verify results
        single_upload(driver, config['single-domain'])
        verify_results(driver, config['single-domain'])

        # Record the end time and calculate duration
        end_time = time.time()
        duration = end_time - start_time

        print(f"User {username} completed the checks in {duration:.2f} seconds.")
        return username, duration
    except Exception as e:
        print(f"Error for user {user_index}: {e}")
        return None, None
    finally:
        driver.quit()

if __name__ == "__main__":
    num_users = 10
    results = []

    # Use ThreadPoolExecutor for concurrent execution
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(perform_user_actions, i) for i in range(num_users)]

        for future in futures:
            try:
                result = future.result()
                if result and result[0]:  # Only append valid results
                    results.append(result)
            except Exception as e:
                print(f"Error during execution: {e}")

    # Print the results for all users
    print("\n--- Test Results ---")
    for username, duration in results:
        print(f"{username}: {duration:.2f} seconds")

    results_dict = {username: f"{duration:.2f} seconds" for username, duration in results}

    with open ('results.json','w') as f:
      json.dump(results_dict,f,indent=4) 
