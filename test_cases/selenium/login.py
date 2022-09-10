from selenium.webdriver.common.by import By
import json
import os
import keyboard
from set_driver import get_driver


def get_credentials():
    THIS_DIR = os.path.dirname(os.path.realpath(__file__))
    with open(f'{THIS_DIR}/admin_credentials.json', 'r') as f:
        admin_credentials = json.load(f)
    return admin_credentials['username'], admin_credentials['password']


def login(driver):
    driver.get("http://127.0.0.1:8000/boat/accounts/login/")
    admin_username, admin_password = get_credentials()
    driver.find_element(By.ID, 'usernameInput').send_keys(admin_username)
    driver.find_element(By.ID, 'passwordInput').send_keys(admin_password)
    driver.find_element(By.ID, 'loginButton').click()

    assert driver.current_url == 'http://127.0.0.1:8000/boat/accounts/home/'


if __name__ == '__main__':
    driver = get_driver()
    driver.get("http://127.0.0.1:8000/boat/")
    login(driver)

    keyboard.wait('esc')

    driver.quit()
