
import glob
import os
import sys
from flask import request, session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import StaleElementReferenceException
from datetime import datetime, timedelta, timezone
import time , json
from utils import   get_url_status ,certificate_checks
import random
import string

def generate_password(length=8):
    # Define character sets
    all_characters = string.ascii_letters + string.digits #+ string.punctuation
    # Generate a random password
    password = ''.join(random.choice(all_characters) for _ in range(length))
    password= f"tes({password})ter"
    return password

# Full path to the ChromeDriver executable file
with open('config.json', 'r') as f:
    config = json.load(f)
url=f"{config['host']}:{config['port']}/"
# Initialize the WebDriver
driver = webdriver.Chrome()

def is_alert_present(): 
    try: 
        driver.switch_to.alert 
        return True 
    except NoAlertPresentException: 
        return False
    
def alert_wait_and_click():
        while is_alert_present()==False: 
            time.sleep(1)
        alert = driver.switch_to.alert
        alert.accept()

def pre_test(unamepass='tester'):
    register(unamepass,unamepass,unamepass)
    login(unamepass,unamepass)

def register(username='tester',password1='tester',password2='tester'):
    # Rgister user tester 
    driver.get(f"{url}/register")
    input_field = driver.find_element("id", "username")
    input_field.send_keys(username)
    input_field = driver.find_element("id", "password1")
    input_field.send_keys(password1)
    input_field = driver.find_element("id", "password2")
    input_field.send_keys(password2)
    button = driver.find_element("class name", "register-submit")
    button.click()
    # waiting for alert to pop up before close
    alert_wait_and_click()



def login(useraname='tester',password='tester'):
    # login user teser 
    driver.get(f"{url}/login")    
    input_field = driver.find_element("id", "username")
    input_field.send_keys(useraname)

    input_field = driver.find_element("id", "password")
    input_field.send_keys(password)

    button = driver.find_element("class name", "login-submit")
    button.click()

def single_upload(domain):
        # settin single domain input    
    time.sleep(5)
    input_field = driver.find_element("id", "single")
    input_field.send_keys(domain)    
    button = driver.find_element("class name", "single-submit")
    button.click()
    alert_wait_and_click()
    time.sleep(5)
    
def verfiy_results(domain):
    # analysing results
    table_body = driver.find_element("id", "resultsBody")
    # Iterate through the rows of the table body
    rows = table_body.find_elements("tag name", "tr")
    for row in rows:
        # Extract cells (td elements) in the row
        cells = row.find_elements("tag name", "td")
        if domain==cells[0].text:
            # Extract text from each cell
            domain = cells[0].text
            status = cells[1].text
            expiration_date = cells[2].text
            issuer = cells[3].text            

    # getting validation data and compare compare with UI 
    status_validation = get_url_status(domain)
    if not  (status_validation =='OK' or status_validation =='FAILED'):     
        sys.exit(1)

    cert=certificate_checks(domain)
    if not (expiration_date == cert[0]):            
        sys.exit(1)    
    if not issuer == cert[1]:
        sys.exit(1)

def test_single_domain_upload_and_verifcation(unamepass='tester'):
    # Rgister user tester 
    pre_test(unamepass)
    single_upload(config['single-domain'])
    verfiy_results(config['single-domain'])    
    

def test_file_upload(unamepass='tester'):
    pre_test(unamepass)    
    time.sleep(5)
    file_input = driver.find_element("id", "bulk")
    file_path = os.path.abspath('./Domains_for_upload.txt')
    
    file_input.send_keys(file_path)  
      
    upload_button = driver.find_element("class name", "bulk-submit") 
    time.sleep(1)
    upload_button.click()
    time.sleep(1)
    
    alert_wait_and_click()
    alert_wait_and_click()

    time.sleep(2)

#def remove_all_domains():
def remove_doamins(domain='ALL',unamepass='tester'):
    pre_test(unamepass)
    time.sleep(2)    
    driver.get(f"{url}//results")  
    time.sleep(2)
    list_group = driver.find_element("id", "domains")
    while True:
        try:
            # Find all list items (li elements) within the list group
            list_items = list_group.find_elements("class name", "list-group-item")
            
            if not list_items:
                break

            for item in list_items:
                try:
                    domain_name = item.text.split("\n")[0]  # Extract the domain name text                    
                    if domain=='ALL' or domain==domain_name:
                        # Re-locate the close button each time to avoid stale element reference
                        close_button = item.find_element("class name", "close")
                        close_button.click()
                        alert_wait_and_click()                        
                    
                    # Wait a little for the DOM to update after removing an item
                    time.sleep(1)

                except StaleElementReferenceException:                    
                    break  # Exit the loop to re-locate all elements

        except StaleElementReferenceException:            
            if domain==domain_name:
                break
            list_group = driver.find_element("id", "domains")            
            continue  # Re-locate the list group and re-enter the loop
def schedule_job(unamepass='tester'):    
    pre_test(unamepass)           
    driver.get(f"{url}/dashboard")     
    time.sleep(5)
    time_input = driver.find_element(By.ID, "schedule-time")
    date_input = driver.find_element(By.ID, "schedule-date")
    interval_input = driver.find_element(By.ID, "interval")    
    # Calculate the time 2 hours earlier than the current time    
    
    future_time = datetime.now(timezone.utc) + timedelta(minutes = 1)    
    
    date_value = future_time.strftime("%d/%m/%Y")  
    time_value = future_time.strftime("%H:%M")           
    
    # Set the value of the datetime-local input field
    date_input.send_keys(date_value)
    time_input.send_keys(time_value)
    interval_input.send_keys('1')
    button = driver.find_element("class name","schedule-submit")
    button.click()
    alert_wait_and_click() 
    time.sleep(60)
    driver.get(f"{url}/results")       
    h3_element = driver.find_element(By.TAG_NAME, 'h3')
    h3_text=h3_element.text
    if  not (date_value in h3_text and  time_value in h3_text): 
        print (h3_text)
        print(f"The <h3> element not contains the string: '{date_value} {time_value}'") 
        exit (1)
    else:
        return True
    time.sleep(2)

def init():
    if os.path.exists('.././userdata/users.json'):
        os.remove('.././userdata/users.json')
    
    pattern = os.path.join('../userdata', 'tester*.json')
    files = glob.glob(pattern)
    for file_path in files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def quit():
# Close the WebDriver
    driver.quit()

if __name__ == "__main__":
    init()
    gp=generate_password()
    # test_single_domain_upload_and_verifcation(gp)
    test_file_upload(gp)  
    schedule_job(gp)
    test_file_upload(gp)  
    remove_doamins('apple.com',gp)  # remove specific doamin 
    remove_doamins('ALL',gp)  # remove all domains 
    quit()

