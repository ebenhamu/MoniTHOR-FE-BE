import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

@pytest.fixture(scope='session')
def driver(request):
    """Set up webdriver fixture."""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(executable_path='geckodriver')  # Replace with the actual path to geckodriver
    driver = webdriver.Firefox(options=options, service=service)
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.implicitly_wait(10)

    yield driver
    driver.quit()

def test_user_registration(driver):
    # Step 1: User Registration
    driver.get('http://127.0.0.1:8080/register')
    driver.find_element(By.NAME, 'Username:').send_keys('Test')
    driver.find_element(By.NAME, 'Password:').send_keys('Test111')
    driver.find_element(By.NAME, 'Confirm Password:').send_keys('Test111')
    driver.find_element(By.CSS_SELECTOR, 'input[type="REGISTER"]').click()
    
    success_message = driver.find_element(By.TAG_NAME, 'body').text
    assert "User registered successfully!" in success_message

    with open('users.json', 'r') as f:
        users = json.load(f)
    assert 'Test' in users
    assert users['Test'] == 'Test111'

def test_user_login(driver):
    # Step 2: User Login
    driver.get('http://127.0.0.1:8080/login')
    driver.find_element(By.NAME, 'Username').send_keys('Test')
    driver.find_element(By.NAME, 'Password').send_keys('Test111')
    driver.find_element(By.CSS_SELECTOR, 'input[type="LOGIN"]').click()
    
    dashboard_message = driver.find_element(By.TAG_NAME, 'h1').text
    assert "Welcome Test" in dashboard_message

    dashboard_status = driver.find_element(By.TAG_NAME, 'p').text
    assert "Secure Session Active" in dashboard_status

def test_secure_session_management(driver):
    # Step 3: Ensure no unauthorized access
    driver.get('http://127.0.0.1:8080/dashboard')
    assert "Secure Session Active" in driver.find_element(By.TAG_NAME, 'body').text

    # Step 4: Logout and check unauthorized access
    driver.get('http://127.0.0.1:8080/logout')
    driver.get('http://127.0.0.1:8080/dashboard')
    assert "Login" in driver.title

    # Step 5: Check session expiration (Simulating with a delay)
    driver.get('http://127.0.0.1:8080/login')
    driver.find_element(By.NAME, 'Username').send_keys('Test')
    driver.find_element(By.NAME, 'Password').send_keys('Test111')
    driver.find_element(By.CSS_SELECTOR, 'input[type="LOGIN"]').click()

    time.sleep(10)  # Adjust the delay based on your session timeout settings
    driver.get('http://127.0.0.1:8080/dashboard')
    assert "Login" in driver.title
