import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import json
import re
import logging
import random

# ===============================
# CONFIG
# ===============================
BASE_DOMAIN = "https://www.bringo.ma"
BASE_URL = "https://www.bringo.ma/fr_MA/store/carrefour-hypermarket-carrefour-sidi-maarouf/mon-marche-8"

STORE_NAME = "Bringo"
CITY_STORE = "Carrefour Sidi Maarouf"
CATEGORY_NAME = "Mon Marche"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# ===============================
# SCRAPING
# ===============================
all_data = []
page = 1
last_page_product_ids = []

while True:

    page_start_time = time.time()

    if page == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}?page={page}"

    logging.info(f"Scraping page {page}")

    response = session.get(url, timeout=10)

    if response.status_code != 200:
        logging.warning("Non-200 status. Stopping.")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", class_="box-product")

    logging.info(f"Page {page} | Products found: {len(products)}")

    if not products:
        logging.info("No products found. Stopping.")
        break

    # Detect pagination end (repeat page)
    current_ids = [p.get("data-cnstrc-item-id") for p in products]
    if page > 1 and current_ids == last_page_product_ids:
        logging.warning("Pagination end detected (repeated products).")
        break

    last_page_product_ids = current_ids

    # ===============================
    # PRODUCT LOOP
    # ===============================
    for product in products:

        product_id = product.get("data-cnstrc-item-id")
        variation_id = product.get("data-cnstrc-item-variation-id")
        name = product.get("data-cnstrc-item-name")

        product_url = None
        weight_g = None
        price_per_kg = None

        # PRODUCT URL
        link_tag = product.find("a", class_="bringo-product-name")
        if link_tag:
            href = link_tag.get("href")
            if href:
                product_url = BASE_DOMAIN + href

        # PRICE EXTRACTION
        original_price = None
        promo_price = None
        discount_percent = None

        if link_tag:
            onclick_data = link_tag.get("onclick", "")
            raw_json = re.search(r'\{.*\}', onclick_data)
            if raw_json:
                try:
                    data_json = json.loads(raw_json.group())
                    original_price = float(data_json.get("initial_price", 0)) / 100
                    promo_price = float(data_json.get("price", 0)) / 100
                    discount_percent = data_json.get("discount_rate")
                except:
                    pass

        if not original_price:
            original_price = promo_price

        # WEIGHT DETECTION
        if name:
            match = re.search(r'(\d+(?:\.\d+)?)\s*(kg|g)', name.lower())
            if match:
                qty, unit = match.groups()
                qty = float(qty)
                weight_g = qty * 1000 if unit == "kg" else qty

        # PRICE PER KG
        if weight_g and promo_price:
            price_per_kg = round((promo_price / weight_g) * 1000, 2)

        # SAVE
        if product_id and promo_price:
            all_data.append({
                "product_id": product_id,
                "variation_id": variation_id,
                "name": name,
                "original_price": original_price,
                "promo_price": promo_price,
                "discount_percent": discount_percent,
                "weight_g": weight_g,
                "price_per_kg": price_per_kg,
                "product_url": product_url,
                "store": STORE_NAME,
                "city_store": CITY_STORE,
                "category": CATEGORY_NAME,
                "page": page,
                "date": datetime.today().strftime("%Y-%m-%d")
            })

    logging.info(f"Page {page} | Collected so far: {len(all_data)}")
    logging.info(f"Page {page} | Time: {round(time.time() - page_start_time, 2)} sec")
    logging.info("=" * 50)

    page += 1
    time.sleep(random.uniform(1.5, 3.5))

# ===============================
# SAVE CSV
# ===============================
df = pd.DataFrame(all_data)
filename = f"bringo_{CATEGORY_NAME.lower().replace(' ', '_')}_all_pages.csv"
df.to_csv(filename, index=False)

logging.info("=" * 50)
logging.info("SCRAPING FINISHED")
logging.info(f"Total pages scraped: {page - 1}")
logging.info(f"Total products collected: {len(df)}")
logging.info("=" * 50)