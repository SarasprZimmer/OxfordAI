from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import os

LOGIN_URL = "http://1to100.ir/admin/login"
USERNAME = os.getenv("OXFORD_USER")
PASSWORD = os.getenv("OXFORD_PASS")

def scrape_admin_table(path, min_columns):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Set default timeout higher
            page.set_default_timeout(60000)

            # Login
            page.goto(LOGIN_URL)
            page.fill("input[name='username']", USERNAME)
            page.fill("input[name='password']", PASSWORD)
            page.click("form button[type='submit']")
            page.wait_for_timeout(2000)

            # Navigate to section
            page.goto(f"http://1to100.ir/admin/{path}")
            page.wait_for_selector("table tbody tr")

            rows = page.query_selector_all("table tbody tr")
            results = []

            for row in rows[:5]:
                cols = row.query_selector_all("td")
                if len(cols) >= min_columns:
                    results.append(" | ".join(col.inner_text().strip() for col in cols[:min_columns]))

            return results

    except PlaywrightTimeout:
        print(f"❌ Timeout while loading {path} table.")
        return ["⏱ اطلاعات بارگذاری نشد. لطفاً دوباره تلاش کنید."]
    except Exception as e:
        print(f"❌ Scraper error: {e}")
        return ["❌ خطا در دریافت اطلاعات."]

    finally:
        try:
            browser.close()
        except:
            pass

def scrape_flights_playwright():
    return scrape_admin_table("flight", 4)

def scrape_hotels_playwright():
    return [f"🏨 {row}" for row in scrape_admin_table("hotels", 2)]

def scrape_tours_playwright():
    return [f"🧳 {row}" for row in scrape_admin_table("tours", 3)]
