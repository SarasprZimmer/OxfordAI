import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

LOGIN_URL = "http://1to100.ir/admin/login"
USERNAME = os.getenv("OXFORD_USER")
PASSWORD = os.getenv("OXFORD_PASS")

def get_admin_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = "/opt/render/project/src/.chromium/chrome-linux/chrome"
    #options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

def login_admin(driver):
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 10)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    password_input = driver.find_element(By.NAME, "password")

    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)

    driver.find_element(By.TAG_NAME, "form").submit()
    time.sleep(2)

def scrape_flights_selenium(driver):
    driver.get("http://1to100.ir/admin/flight")
    time.sleep(2)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    flights = []
    for row in rows[:5]:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 4:
            flights.append(f"{cols[0].text.strip()} → {cols[1].text.strip()} | {cols[2].text.strip()} | {cols[3].text.strip()}")
    return flights

def scrape_hotels_selenium(driver):
    driver.get("http://1to100.ir/admin/hotels")
    time.sleep(2)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    hotels = []
    for row in rows[:5]:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 2:
            hotels.append(f"🏨 {cols[0].text.strip()} | {cols[1].text.strip()}")
    return hotels

def scrape_tours_selenium(driver):
    driver.get("http://1to100.ir/admin/tours")
    time.sleep(2)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    tours = []
    for row in rows[:5]:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 3:
            tours.append(f"🧳 {cols[0].text.strip()} | {cols[1].text.strip()} | {cols[2].text.strip()}")
    return tours
