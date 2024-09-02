import random
import string
import os
import json
import subprocess
import sys
import asyncio
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.options import Options

required_packages = [
    'selenium',
    'tqdm'
]
EMAIL_CONFIG_FILE = 'config.json'
SETTINGS_FILE = 'settings.json'
SAVED_CREDS_FILE = 'accounts.txt'

def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

async def check_and_install_packages():
    not_installed = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            not_installed.append(package)

    if not_installed:
        print('\nInstalling missing packages...')
        for package in tqdm(not_installed, desc='Installing packages', unit='package'):
            install(package)

def load_browser_choice():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file).get('browser', None)
    return None

def save_browser_choice(browser):
    with open(SETTINGS_FILE, 'w') as file:
        json.dump({"browser": browser}, file)

async def choose_browser():
    browser = load_browser_choice()

    if not browser:
        print("Select a browser:")
        print("1. Chrome")
        print("2. Firefox")
        print("3. Edge")
        
        choice = input("Enter your selection number (1-3): ")
        if choice == "1":
            browser = "chrome"
        elif choice == "2":
            browser = "firefox"
        elif choice == "3":
            browser = "edge"
        else:
            print("Wrong choice, Chrome will be used by default.")
            browser = "chrome"
        
        save_choice = input("Would you like to save this browser choice for future use? (y/n): ").strip().lower()
        if save_choice == 'y':
            save_browser_choice(browser)
    
    return browser

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))

def generate_username(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def generate_email_with_single_dots(base_email):
    username, domain = base_email.split('@')
    new_username = []

    for char in username:
        new_username.append(char)
        if random.choice([True, False]) and (len(new_username) > 1 and new_username[-2] != '.'):
            new_username.append('.')
    if new_username[-1] == '.':
        new_username.pop()
    return ''.join(new_username) + f"@{domain}"

def load_email_config(config_file):
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            return json.load(file).get('emails', [])
    return []

def save_email_config(config_file, email):
    emails = load_email_config(config_file)
    if email not in emails:
        emails.append(email)
    with open(config_file, 'w') as file:
        json.dump({"emails": emails}, file)

def get_email(email_config_file):
    email_list = load_email_config(email_config_file)

    if email_list:
        print("Available emails:")
        for i, email in enumerate(email_list):
            print(f"{i + 1}. {email}")

        choice = input("Would you like to use one of these emails? (number/n): ")
        if choice.lower() == 'n':
            user_email = input("Enter your email address: ")
            save_email_config(email_config_file, user_email)
            return user_email
        elif choice.isdigit() and 0 < int(choice) <= len(email_list):
            return email_list[int(choice) - 1]
    user_email = input("Enter your email address: ")
    save_email_config(email_config_file, user_email)
    return user_email

async def automate_registration(email, username, password, driver):
    try:
        driver.get('https://account.spacestation14.com/Identity/Account/Register')

        username_field = driver.find_element(By.NAME, 'Input.Username')
        email_field = driver.find_element(By.NAME, 'Input.Email')
        password_field = driver.find_element(By.NAME, 'Input.Password')
        confirm_password_field = driver.find_element(By.NAME, 'Input.ConfirmPassword')

        username_field.send_keys(username)
        email_field.send_keys(email)
        password_field.send_keys(password)
        confirm_password_field.send_keys(password)

        age_check = driver.find_element(By.NAME, 'Input.AgeCheck')
        if not age_check.is_selected():
            age_check.click()
            
        iframe = driver.find_element(By.XPATH, '//iframe[contains(@src, "hcaptcha.com")]')
        driver.switch_to.frame(iframe)

        checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div#checkbox'))
        )
        checkbox.click()

        driver.switch_to.default_content()
        
        print("Please enter the CAPTCHA yourself and click the registration button.")

        registration_button_xpath = '//button[contains(text(), "Register")]'
        WebDriverWait(driver, 120).until(
            EC.element_to_be_clickable((By.XPATH, registration_button_xpath))
        )
        WebDriverWait(driver, 120).until(
            EC.staleness_of(driver.find_element(By.XPATH, registration_button_xpath))
        )
        print("Registration complete.")
    except Exception as e:
        print(f"Registration Error: {e}")
    finally:
        driver.quit()

async def main():
    await check_and_install_packages()
    browser_choice = await choose_browser()

    auto_generate_username = input("Do you want to automatically generate a username? (y/n): ").strip().lower() == 'y'
    if auto_generate_username:
        username = generate_username()
        print(f"Generated username: {username}")
    else:
        username = input("Enter your username: ")

    password = generate_password()
    chosen_email = get_email(EMAIL_CONFIG_FILE)
    email_with_single_dots = generate_email_with_single_dots(chosen_email)

    print(f"Email: {email_with_single_dots}")
    print(f"Password: {password}")

    driver = None
    while driver is None:
        try:
            if browser_choice == "chrome":
                options = Options()
                driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            elif browser_choice == "firefox":
                driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
            elif browser_choice == "edge":
                driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
            else:
                print("Incorrect browser selection. Try again.")
        except Exception as e:
            print(f"Driver initialization error: {e}. Try again.")

    with open(SAVED_CREDS_FILE, 'a') as f:
        f.write(f'username: {username}\n')
        f.write(f'password: {password}\n')
        f.write(f'email: {email_with_single_dots}\n')

    await automate_registration(email_with_single_dots, username, password, driver)

if __name__ == "__main__":
    asyncio.run(main())
