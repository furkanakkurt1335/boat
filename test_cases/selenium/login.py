from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import json, os, time, keyboard

driver = webdriver.Chrome(service=ChromeService(executable_path=ChromeDriverManager().install()))

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
with open(f'{THIS_DIR}/admin_credentials.json', 'r') as f:
    admin_credentials = json.load(f)
admin_username, admin_password = admin_credentials['username'], admin_credentials['password']

driver.get("http://127.0.0.1:8000/boat/")

def login():
    driver.get("http://127.0.0.1:8000/boat/accounts/login/")
    driver.find_element(By.ID, 'usernameInput').send_keys(admin_username)
    driver.find_element(By.ID, 'passwordInput').send_keys(admin_password)
    driver.find_element(By.ID, 'loginButton').click()

    assert driver.current_url == 'http://127.0.0.1:8000/boat/accounts/home/'

login()

keyboard.wait('esc')

driver.quit()
