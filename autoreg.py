import random
import string
import os
import json
import subprocess
import sys
import asyncio
import http.client
import re
import time
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

#На Csh за Марсель не банят?

SETTINGS_FILE = 'settings.json'
SAVED_CREDS_FILE = 'accounts.txt'

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

def fetch_email():
    conn = http.client.HTTPSConnection("temp-mail44.p.rapidapi.com")

    payload = "{\"key1\":\"value\",\"key2\":\"value\"}"

    headers = {
        'x-rapidapi-key': "7d08ad6be7msh9fd48b2a2ab7c35p118242jsn6346a6c13bc1",
        'x-rapidapi-host': "temp-mail44.p.rapidapi.com",
        'Content-Type': "application/json"
    }

    conn.request("POST", "/api/v3/email/new", payload, headers)

    res = conn.getresponse()
    data = res.read()

    response_json = json.loads(data.decode("utf-8"))

    return response_json.get('email', '')

def extract_word_in_parentheses(text):
    match = re.search(r'\((.*?)\)', text)
    if match:
        word = match.group(1)
        word = word.replace('\\u0026', '&')  
        return word
    return None

def send_extracted_word(word):
    if word:
        print(f'Sending extracted word: {word}')
    else:
        print('No word found in parentheses.')

def check_inbox(email):
    time.sleep(30)
    conn = http.client.HTTPSConnection("temp-mail44.p.rapidapi.com")

    headers = {
        'x-rapidapi-key': "7d08ad6be7msh9fd48b2a2ab7c35p118242jsn6346a6c13bc1",
        'x-rapidapi-host': "temp-mail44.p.rapidapi.com"
    }

    conn.request("GET", f"/api/v3/email/{email}/messages", headers=headers)

    res = conn.getresponse()
    data = res.read()

    inbox_data = data.decode("utf-8")
    print("Inbox data:", inbox_data)

    word = extract_word_in_parentheses(inbox_data)
    
    send_extracted_word(word)

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
    browser_choice = await choose_browser()

    auto_generate_username = input("Do you want to automatically generate a username? (y/n): ").strip().lower() == 'y'
    if auto_generate_username:
        username = generate_username()
        print(f"Generated username: {username}")
    else:
        username = input("Enter your username: ")

    password = generate_password()
    email = fetch_email()

    print(f"Email: {email}")
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
        f.write(f'email: {email}\n')

    await automate_registration(email, username, password, driver)
    
    check_inbox(email)

if __name__ == "__main__":
    asyncio.run(main())
