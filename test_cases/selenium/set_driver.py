from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=chrome_options, service=ChromeService(executable_path=ChromeDriverManager().install()))
