from login import login
from set_driver import get_driver
from selenium.webdriver.common.by import By
import keyboard
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--treebank-title', action='store', required=True)
    args = parser.parse_args()
    tb_title = args.treebank_title

    driver = get_driver()

    login(driver)

    driver.find_element(By.ID, 'treebanksDropdownMenuButton').click()

    driver.find_element(By.ID, 'view_treebanks').click()

    driver.find_element(By.ID, tb_title).find_element(
        By.ID, 'trash').click()

    driver.implicitly_wait(10)

    driver.find_element(By.ID, 'modalDeleteButton').click()

    driver.find_element(By.ID, 'treebanksDropdownMenuButton').click()

    driver.find_element(By.ID, 'view_treebanks').click()

    try:
        driver.find_element(By.ID, tb_title)
    except:
        print('Treebank deleted!')

    keyboard.wait('esc')

    driver.quit()
