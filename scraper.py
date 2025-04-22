import os
import asyncio
from playwright.async_api import async_playwright

LOGIN_URL = "http://1to100.ir/admin/login"
USERNAME = os.getenv("OXFORD_USER")
PASSWORD = os.getenv("OXFORD_PASS")

semaphore = asyncio.Semaphore(5)  # Limit concurrent scrapes

async def scrape_admin_table(path, min_columns):
    async with semaphore:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(LOGIN_URL)
                await page.fill("input[name='username']", USERNAME)
                await page.fill("input[name='password']", PASSWORD)
                await page.click("form button[type='submit']")
                await page.wait_for_timeout(1500)

                await page.goto(f"http://1to100.ir/admin/{path}")
                await page.wait_for_selector("table tbody tr")
                rows = await page.query_selector_all("table tbody tr")

                results = []
                for row in rows[:5]:
                    cols = await row.query_selector_all("td")
                    if len(cols) >= min_columns:
                        text = [await col.inner_text() for col in cols[:min_columns]]
                        results.append(" | ".join(t.strip() for t in text))

                await browser.close()
                return results
        except Exception as e:
            print("❌ Scraper error:", e)
            return ["در حال حاضر دسترسی به اطلاعات ممکن نیست."]

async def scrape_flights_playwright():
    return await scrape_admin_table("flight", 4)

async def scrape_hotels_playwright():
    data = await scrape_admin_table("hotels", 2)
    return [f"🏨 {row}" for row in data]

async def scrape_tours_playwright():
    data = await scrape_admin_table("tours", 3)
    return [f"🧳 {row}" for row in data]
