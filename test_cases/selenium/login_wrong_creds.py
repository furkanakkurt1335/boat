from selenium.webdriver.common.by import By
import keyboard
from set_driver import get_driver


def login(driver):
    driver.get("http://127.0.0.1:8000/boat/accounts/login/")
    admin_username, admin_password = 'username436859', 'password4357843'
    driver.find_element(By.ID, 'usernameInput').send_keys(admin_username)
    driver.find_element(By.ID, 'passwordInput').send_keys(admin_password)
    driver.find_element(By.ID, 'loginButton').click()

    assert driver.current_url == 'http://127.0.0.1:8000/boat/accounts/login/'
    driver.find_element(
        By.XPATH, "//*[contains(text(),'User not found with these credentials.')]")


if __name__ == '__main__':
    driver = get_driver()
    driver.get("http://127.0.0.1:8000/boat/")
    login(driver)

    keyboard.wait('esc')

    driver.quit()
