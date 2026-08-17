"""
scraper.py

Fetches a single company's page from dsebd.org and extracts:
  - Latest Trading Price
  - Forward P/E  (from "Current P/E Ratio using Basic EPS", last/latest column)
  - Trailing P/E (from "Trailing P/E Ratio", last/latest column)
  - The full "Interim Financial Performance" table (EPS breakdown), kept
    exactly as it appears on the site (including its merged header cells)

Built and verified against real page HTML from dsebd.org (BRACBANK).
"""

import re
import warnings

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}


def fetch_html(ticker):
    """
    Fetches the raw HTML for a ticker's DSE page. Falls back to skipping
    certificate verification if the office network's SSL inspection
    blocks the normal verified request (see inspect_dse_page.py notes).
    """
    url = f"https://www.dsebd.org/displayCompany.php?name={ticker}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
    except requests.exceptions.SSLError:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        response = requests.get(url, headers=HEADERS, timeout=20, verify=False)
    response.raise_for_status()
    return response.text


def _find_table_after_heading(soup, heading_substring):
    """
    Finds the first <h2> whose text contains heading_substring, then
    returns the next <table> that follows it in the document. This is
    more reliable than table position/index, since the page has many
    tables that all share the same id="company".
    """
    for h2 in soup.find_all("h2"):
        if heading_substring in h2.get_text():
            table = h2.find_next("table")
            if table:
                return table
    return None


def get_latest_price(soup):
    """Reads 'Last Trading Price' from the Market Information table."""
    for th in soup.find_all("th"):
        if th.get_text(strip=True) == "Last Trading Price":
            td = th.find_next_sibling("td")
            if td:
                try:
                    return float(td.get_text(strip=True))
                except ValueError:
                    return None
    return None


def get_pe_ratios(soup):
    """
    Reads Forward P/E and Trailing P/E from the "...based on latest
    Un-audited Financial Statements" table (NOT the Audited one - the
    page has both, with near-identical structure).
    """
    table = _find_table_after_heading(soup, "based on latest Un-audited Financial Statements")
    if table is None:
        return {"forward_pe": None, "trailing_pe": None}

    forward_pe = None
    trailing_pe = None

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        label = cells[0].get_text(separator=" ", strip=True)
        if not cells[1:]:
            continue
        last_value_text = cells[-1].get_text(strip=True)

        if label.startswith("Current P/E Ratio using Basic EPS"):
            forward_pe = _to_float(last_value_text)
        elif label == "Trailing P/E Ratio":
            trailing_pe = _to_float(last_value_text)

    return {"forward_pe": forward_pe, "trailing_pe": trailing_pe}


def get_interim_table_html(soup):
    """
    Returns the full "Interim Financial Performance" table's HTML,
    unchanged - so it can be displayed exactly as it appears on the
    DSE site (preserves the merged quarter/year header cells).
    """
    table = _find_table_after_heading(soup, "Interim Financial Performance")
    return str(table) if table is not None else None


def _to_float(text):
    text = text.strip()
    if text in ("", "-", "N/A"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def get_company_data(ticker):
    """
    Fetches everything for one ticker and returns a dict:
      ticker, latest_price, forward_pe, trailing_pe, interim_table_html
    """
    html = fetch_html(ticker)
    soup = BeautifulSoup(html, "lxml")

    pe = get_pe_ratios(soup)
    return {
        "ticker": ticker,
        "latest_price": get_latest_price(soup),
        "forward_pe": pe["forward_pe"],
        "trailing_pe": pe["trailing_pe"],
        "interim_table_html": get_interim_table_html(soup),
    }
