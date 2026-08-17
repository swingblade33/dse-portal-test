"""
target_price_store.py

Simple persistent storage for analyst-set target prices. Uses a plain
JSON file - no database needed for a 5-company demo (see the earlier
discussion: this only needs to survive between runs on the SAME
machine; if/when this moves to Streamlit Community Cloud, this file
will need to move to a real persistent store, since Streamlit Cloud's
local disk isn't guaranteed to survive restarts).
"""

import json
import os

STORE_PATH = os.path.join(os.path.dirname(__file__), "target_prices.json")

DEFAULT_TARGET_PRICES = {
    "BRACBANK": 84.6,
    "CITYBANK": 38.4,
    "BXPHARMA": 176,
    "GP": 291,
    "OLYMPIC": 170,
}


def load_target_prices():
    """Returns {ticker: target_price}. Creates the file with defaults if missing."""
    if not os.path.exists(STORE_PATH):
        save_target_prices(DEFAULT_TARGET_PRICES)
        return dict(DEFAULT_TARGET_PRICES)

    with open(STORE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_target_prices(prices: dict):
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(prices, f, indent=2)


def update_target_price(ticker, new_price):
    prices = load_target_prices()
    prices[ticker] = new_price
    save_target_prices(prices)
