from playwright.sync_api import sync_playwright
import os

def scrape_flights_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("http://1to100.ir/admin/login")
        page.fill("input[name='username']", os.getenv("OXFORD_USER"))
        page.fill("input[name='password']", os.getenv("OXFORD_PASS"))
        page.click("form button[type='submit']")
        page.wait_for_timeout(2000)

        page.goto("http://1to100.ir/admin/flight")
        page.wait_for_selector("table tbody tr")
        rows = page.query_selector_all("table tbody tr")

        flights = []
        for row in rows[:5]:
            cols = row.query_selector_all("td")
            if len(cols) >= 4:
                flights.append(f"{cols[0].inner_text().strip()} → {cols[1].inner_text().strip()} | {cols[2].inner_text().strip()} | {cols[3].inner_text().strip()}")

        browser.close()
        return flights

def scrape_hotels_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("http://1to100.ir/admin/login")
        page.fill("input[name='username']", os.getenv("OXFORD_USER"))
        page.fill("input[name='password']", os.getenv("OXFORD_PASS"))
        page.click("form button[type='submit']")
        page.wait_for_timeout(2000)

        page.goto("http://1to100.ir/admin/hotels")
        page.wait_for_selector("table tbody tr")
        rows = page.query_selector_all("table tbody tr")

        hotels = []
        for row in rows[:5]:
            cols = row.query_selector_all("td")
            if len(cols) >= 2:
                hotels.append(f"🏨 {cols[0].inner_text().strip()} | {cols[1].inner_text().strip()}")

        browser.close()
        return hotels

def scrape_tours_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("http://1to100.ir/admin/login")
        page.fill("input[name='username']", os.getenv("OXFORD_USER"))
        page.fill("input[name='password']", os.getenv("OXFORD_PASS"))
        page.click("form button[type='submit']")
        page.wait_for_timeout(2000)

        page.goto("http://1to100.ir/admin/tours")
        page.wait_for_selector("table tbody tr")
        rows = page.query_selector_all("table tbody tr")

        tours = []
        for row in rows[:5]:
            cols = row.query_selector_all("td")
            if len(cols) >= 3:
                tours.append(f"🧳 {cols[0].inner_text().strip()} | {cols[1].inner_text().strip()} | {cols[2].inner_text().strip()}")

        browser.close()
        return tours
