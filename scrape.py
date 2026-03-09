# sheets.py
import os
import json
import logging
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# ── Google Sheets config ──────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Sheet columns (must match the order in _row_from_product)
HEADERS = [
    "product_id", "variation_id", "name",
    "original_price", "promo_price", "discount_percent",
    "weight_g", "price_per_kg", "product_url",
    "store", "city_store", "category", "page", "date"
]


def _get_client() -> gspread.Client:
    """
    Build a gspread client from credentials.
    Priority:
      1. GOOGLE_CREDENTIALS_JSON env var  (JSON string — ideal for Render)
      2. GOOGLE_CREDENTIALS_FILE env var  (path to a local .json file)
    """
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE")

    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif creds_file:
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    else:
        raise EnvironmentError(
            "No Google credentials found. "
            "Set GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_FILE."
        )

    return gspread.authorize(creds)


def _get_or_create_worksheet(
    spreadsheet: gspread.Spreadsheet,
    tab_name: str
) -> gspread.Worksheet:
    """Return the worksheet with tab_name, creating it (with headers) if absent."""
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=5000, cols=len(HEADERS))
        ws.append_row(HEADERS, value_input_option="RAW")
        logger.info(f"Created new worksheet: {tab_name}")
    return ws


def _row_from_product(p: dict) -> list:
    """Convert a product dict to an ordered list matching HEADERS."""
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


def save_to_sheets(products: list[dict]) -> int:
    """
    Append scraped products to Google Sheets.

    Sheet layout:
      • One spreadsheet identified by env var GOOGLE_SHEET_ID
        (share it with the service-account email first!)
      • One tab per scrape date  →  e.g. "2026-03-09"
        (change TAB_MODE below to "fixed" to always use a single tab)

    Returns the number of rows written.
    """
    if not products:
        return 0

    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise EnvironmentError("GOOGLE_SHEET_ID env var is not set.")

    # Tab strategy: daily tab  (set to any fixed string for a single tab)
    TAB_MODE = os.environ.get("SHEETS_TAB_MODE", "daily")   # "daily" | "fixed"
    FIXED_TAB = os.environ.get("SHEETS_TAB_NAME", "Products")

    tab_name = datetime.today().strftime("%Y-%m-%d") if TAB_MODE == "daily" else FIXED_TAB

    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    ws = _get_or_create_worksheet(spreadsheet, tab_name)

    # Build rows and batch-append (much faster than one row at a time)
    rows = [_row_from_product(p) for p in products]
    ws.append_rows(rows, value_input_option="USER_ENTERED")

    logger.info(f"Saved {len(rows)} rows to sheet '{sheet_id}' tab '{tab_name}'")
    return len(rows)
