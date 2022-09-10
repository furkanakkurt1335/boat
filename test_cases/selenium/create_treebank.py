from login import login
from set_driver import get_driver
from selenium.webdriver.common.by import By
import keyboard
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--treebank-title', action='store', required=True)
    parser.add_argument('--treebank-lang', action='store', required=True)
    args = parser.parse_args()
    tb_title = args.treebank_title
    tb_lang = args.treebank_lang

    driver = get_driver()

    login(driver)

    driver.find_element(By.ID, 'treebanksDropdownMenuButton').click()

    driver.find_element(By.ID, 'create_treebank').click()

    driver.find_element(By.ID, 'title').send_keys(tb_title)

    driver.find_element(By.ID, 'language').send_keys(tb_lang)

    driver.find_element(By.ID, 'create').click()

    driver.implicitly_wait(10)

    driver.find_element(By.ID, 'treebanksDropdownMenuButton').click()

    driver.find_element(By.ID, 'view_treebanks').click()

    # asserts the treebank exists by trying to find it
    driver.find_element(By.ID, tb_title)

    keyboard.wait('esc')

    driver.quit()
