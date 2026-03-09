# sheets.py
import os
import json
import logging
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "product_id", "variation_id", "name",
    "original_price", "promo_price", "discount_percent",
    "weight_g", "price_per_kg", "product_url",
    "store", "city_store", "category", "page", "date"
]

def _get_client():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif creds_file:
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    else:
        raise EnvironmentError("No Google credentials found. Set GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_FILE.")
    return gspread.authorize(creds)

def _get_or_create_worksheet(spreadsheet, tab_name):
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=5000, cols=len(HEADERS))
        ws.append_row(HEADERS, value_input_option="RAW")
        logger.info(f"Created new worksheet: {tab_name}")
    return ws

def _row_from_product(p):
    return [
        p.get("product_id"),
        p.get("variation_id"),
        p.get("name"),
        p.get("original_price"),
        p.get("promo_price"),
        p.get("discount_percent"),
        p.get("weight_g"),
        p.get("price_per_kg"),
        p.get("product_url"),
        p.get("store"),
        p.get("city_store"),
        p.get("category"),
        p.get("page"),
        p.get("date"),
    ]

def save_to_sheets(products):
    if not products:
        return 0
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise EnvironmentError("GOOGLE_SHEET_ID env var is not set.")
    TAB_MODE = os.environ.get("SHEETS_TAB_MODE", "daily")
    FIXED_TAB = os.environ.get("SHEETS_TAB_NAME", "Products")
    tab_name = datetime.today().strftime("%Y-%m-%d") if TAB_MODE == "daily" else FIXED_TAB
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    ws = _get_or_create_worksheet(spreadsheet, tab_name)
    rows = [_row_from_product(p) for p in products]
    ws.append_rows(rows, value_input_option="USER_ENTERED")
    logger.info(f"Saved {len(rows)} rows to sheet '{sheet_id}' tab '{tab_name}'")
    return len(rows)
