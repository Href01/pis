# app.py
import time
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from scrape import run
from sheets import save_to_sheets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow all origins


@app.route("/")
def index():
    return jsonify({
        "service": "Bringo Scraper",
        "status": "running",
        "endpoints": {
            "/scrape": "Launch a full scrape and save to Google Sheets",
            "/health": "Check service health"
        }
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


@app.route("/scrape")
def scrape_endpoint():
    start_time = time.time()
    today = datetime.today().strftime("%Y-%m-%d")
    logger.info("Scrape triggered")
    try:
        data = run()
        duration = round(time.time() - start_time, 2)
        if not data:
            logger.warning("Scrape returned no products")
            return jsonify({
                "status": "success",
                "products_scraped": 0,
                "message": "No products found.",
                "duration_seconds": duration
            })
        rows_saved = save_to_sheets(data)
        pages = data[-1]["page"] if data else 0
        logger.info(f"Scrape complete | products={len(data)} | pages={pages} | duration={duration}s")
        return jsonify({
            "status": "success",
            "products_scraped": len(data),
            "rows_saved_to_sheets": rows_saved,
            "pages_scraped": pages,
            "tab_name": today,
            "store": data[0]["store"],
            "city_store": data[0]["city_store"],
            "category": data[0]["category"],
            "duration_seconds": duration
        })
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"Scrape failed after {duration}s: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "duration_seconds": duration
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
