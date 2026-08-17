"""
app.py

DSE Investor Portal - Demo (5 companies)

A single-page interface showing, for each tracked company:
  - Latest Trading Price (live from dsebd.org)
  - Forward P/E and Trailing P/E (live from dsebd.org)
  - Target Price (editable directly on the page, saved persistently)
  - Upside Potential = (Target Price / Latest Price) - 1

Plus a per-company view of the full Interim Financial Performance
(EPS) table, shown exactly as it appears on the DSE site.

RUN LOCALLY (from VS Code terminal):
    pip install streamlit requests beautifulsoup4 lxml
    streamlit run app.py
"""

import streamlit as st
import scraper
import target_price_store

TICKERS = ["BRACBANK", "CITYBANK", "BXPHARMA", "GP", "OLYMPIC"]

st.set_page_config(page_title="DSE Investor Portal - Demo", layout="wide")


@st.cache_data(ttl=300, show_spinner=False)
def get_live_data(ticker):
    """
    Cached for 5 minutes so we're not hammering dsebd.org on every
    interaction - each user action (like editing a target price)
    triggers a Streamlit rerun, and without caching that would mean
    a fresh scrape of all 5 companies every single time.
    """
    try:
        return scraper.get_company_data(ticker), None
    except Exception as e:
        return None, str(e)


st.title("DSE Investor Portal - Demo")
st.caption("Live data from the Dhaka Stock Exchange. Target prices are set by analysts and can be updated below.")

if st.button("Refresh live data now"):
    get_live_data.clear()

target_prices = target_price_store.load_target_prices()

st.subheader("Overview")

header_cols = st.columns([1.3, 1.2, 1.2, 1.2, 1.3, 1.3])
for col, label in zip(header_cols, ["Ticker", "Latest Price", "Forward P/E", "Trailing P/E",
                                     "Target Price", "Upside Potential"]):
    col.markdown(f"**{label}**")

for ticker in TICKERS:
    data, error = get_live_data(ticker)
    cols = st.columns([1.3, 1.2, 1.2, 1.2, 1.3, 1.3])

    cols[0].write(ticker)

    if error:
        cols[1].write("Error")
        cols[2].write("-")
        cols[3].write("-")
        cols[4].write("-")
        cols[5].write("-")
        st.caption(f"{ticker}: could not fetch live data ({error})")
        continue

    latest_price = data["latest_price"]
    forward_pe = data["forward_pe"]
    trailing_pe = data["trailing_pe"]

    cols[1].write(f"{latest_price:.2f}" if latest_price is not None else "N/A")
    cols[2].write(f"{forward_pe:.2f}" if forward_pe is not None else "N/A")
    cols[3].write(f"{trailing_pe:.2f}" if trailing_pe is not None else "N/A")

    current_target = target_prices.get(ticker, 0.0)
    new_target = cols[4].number_input(
        "Target Price", value=float(current_target), key=f"target_{ticker}",
        label_visibility="collapsed", step=0.1, format="%.2f",
    )
    if new_target != current_target:
        target_price_store.update_target_price(ticker, new_target)
        target_prices[ticker] = new_target
        st.rerun()

    if latest_price:
        upside = (new_target / latest_price) - 1
        cols[5].write(f"{upside * 100:.2f}%")
    else:
        cols[5].write("N/A")

st.divider()
st.subheader("Interim Financial Performance (EPS)")
selected_ticker = st.selectbox("Choose a company", TICKERS)

data, error = get_live_data(selected_ticker)
if error:
    st.warning(f"Could not fetch data for {selected_ticker}: {error}")
elif data["interim_table_html"]:
    st.markdown(data["interim_table_html"], unsafe_allow_html=True)
else:
    st.write("No Interim Financial Performance table found for this company.")
