from flask import Flask, jsonify
from scraper import get_admin_driver, login_admin, scrape_flights_selenium, scrape_hotels_selenium, scrape_tours_selenium

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Scraper API is running"

@app.route("/flights", methods=["GET"])
def flights():
    print("🔍 /flights endpoint hit")
    try:
        driver = get_admin_driver()
        print("✅ Driver started")
        login_admin(driver)
        print("✅ Logged in")
        flights = scrape_flights_selenium(driver)
        print("✅ Flights scraped:", flights)
        driver.quit()
        return jsonify({"flights": flights}), 200
    except Exception as e:
        print("❌ Error during /flights scraping:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/hotels", methods=["GET"])
def hotels():
    print("🔍 /hotels endpoint hit")
    try:
        driver = get_admin_driver()
        print("✅ Driver started")
        login_admin(driver)
        print("✅ Logged in")
        hotels = scrape_hotels_selenium(driver)
        print("✅ Hotels scraped:", hotels)
        driver.quit()
        return jsonify({"hotels": hotels}), 200
    except Exception as e:
        print("❌ Error during /hotels scraping:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/tours", methods=["GET"])
def tours():
    print("🔍 /tours endpoint hit")
    try:
        driver = get_admin_driver()
        print("✅ Driver started")
        login_admin(driver)
        print("✅ Logged in")
        tours = scrape_tours_selenium(driver)
        print("✅ Tours scraped:", tours)
        driver.quit()
        return jsonify({"tours": tours}), 200
    except Exception as e:
        print("❌ Error during /tours scraping:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
