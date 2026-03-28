"""
Tick-by-Tick Data Downloader using Alpaca Markets API
Downloads all historical trades for x company
and saves them to CSV files split by year.

Requirements:
    pip install pandas requests

Setup:
    1. Sign up at https://alpaca.markets (free paper account)
    2. Get your API keys from the dashboard
    3. Replace API_KEY and API_SECRET below
"""

import requests
import pandas as pd
import time
import os
from datetime import datetime, date
from tools import add_diff

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_KEY    = "Insert your API key here"
API_SECRET = "Insert your API secret here"
BASE_URL   = "https://data.alpaca.markets/v2"

SYMBOL     = "UNH" #Change to the desired stock symbol (e.g., AAPL, MSFT, etc.)
START_DATE = "2020-01-01"
END_DATE   = "2024-12-31"
OUTPUT_DIR = "./unh_tick_data" #change to your desired output directory

# How many trades to fetch per request (max 10000)
LIMIT      = 10_000

# Seconds to wait between requests to avoid rate limiting
RATE_LIMIT_SLEEP = 0.3
# ─────────────────────────────────────────────────────────────────────────────


def get_headers():
    return {
        "APCA-API-KEY-ID": API_KEY,
        "APCA-API-SECRET-KEY": API_SECRET,
    }


def fetch_trades_page(symbol, start, end, page_token=None):
    """Fetch a single page of tick data."""
    params = {
        "start":  start,
        "end":    end,
        "limit":  LIMIT,
        "feed":   "iex",   # free tier: iex | paid tier: sip (full market)
    }
    if page_token:
        params["page_token"] = page_token

    url = f"{BASE_URL}/stocks/{symbol}/trades"

    response = requests.get(url, headers=get_headers(), params=params)

    if response.status_code == 429:
        print("  Rate limited — sleeping 10 seconds...")
        time.sleep(10)
        return fetch_trades_page(symbol, start, end, page_token)

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    return response.json()


def fetch_all_trades_for_year(symbol, year):
    """Fetch all tick data for a given year, handling pagination."""
    start = f"{year}-01-01T00:00:00Z"
    end   = f"{year}-12-31T23:59:59Z"

    print(f"\n📅 Fetching {symbol} tick data for {year}...")

    all_trades = []
    page_token = None
    page_num   = 0

    while True:
        page_num += 1
        print(f"  Page {page_num} | Trades collected so far: {len(all_trades):,}", end="\r")

        data = fetch_trades_page(symbol, start, end, page_token)

        trades = data.get("trades", [])
        if trades:
            all_trades.extend(trades)

        page_token = data.get("next_page_token")
        if not page_token:
            break  # No more pages

        time.sleep(RATE_LIMIT_SLEEP)

    print(f"  ✅ Done — {len(all_trades):,} trades fetched for {year}        ")
    return all_trades


def trades_to_dataframe(trades):
    """Convert raw trade list to a clean DataFrame."""
    df = pd.DataFrame(trades)

    if df.empty:
        return df

    # Rename columns to readable names
    df = df.rename(columns={
        "t": "timestamp",
        "x": "exchange",
        "p": "price",
        "s": "size",
        "i": "trade_id",
        "c": "conditions",
        "z": "tape",
    })

    df["timestamp"] = pd.to_datetime(df["timestamp"], format='mixed', utc=True)

    df = df.sort_values("timestamp").reset_index(drop=True)

    # Keep only the most useful columns
    cols = ["timestamp", "price", "size", "exchange", "trade_id", "conditions", "tape"]
    df = df[[c for c in cols if c in df.columns]]


    return df


def save_year(df, symbol, year, output_dir):
    """Save a year's worth of data to CSV."""
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{symbol}_ticks_{year}.csv")
    df.to_csv(filename, index=False)
    size_mb = os.path.getsize(filename) / (1024 * 1024)
    print(f"  💾 Saved: {filename} ({size_mb:.1f} MB)")
    return filename


def main():
    print("=" * 60)
    print(f"  Alpaca Tick Data Downloader")
    print(f"  Symbol : {SYMBOL}")
    print(f"  Period : {START_DATE} → {END_DATE}")
    print(f"  Feed   : IEX (free) — switch to 'sip' for paid plan")
    print("=" * 60)

    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n❌ ERROR: Please set your API_KEY and API_SECRET at the top of the script.")
        print("   Sign up free at https://alpaca.markets\n")
        return

    start_year = int(START_DATE[:4])
    end_year   = int(END_DATE[:4])

    saved_files = []

    for year in range(start_year, end_year + 1):
        filepath = os.path.join(OUTPUT_DIR, f"{SYMBOL}_ticks_{year}.csv")
        if os.path.exists(filepath):
            print(f"⏩ Skipping {year} — file already exists")
            continue

        try:                          # ← indented once under for
            trades = fetch_all_trades_for_year(SYMBOL, year)

            if not trades:
                print(f"  ⚠ No trades found for {year}")
                continue

            df = trades_to_dataframe(trades)
            filepath = save_year(df, SYMBOL, year, OUTPUT_DIR)
            saved_files.append(filepath)
            df = add_diff(filepath)
        

        except Exception as e:        # ← must match the try
            print(f"\n❌ Error fetching {year}: {e}")
            continue

    print("\n" + "=" * 60)
    print("  ✅ Download complete!")
    print(f"  Files saved to: {os.path.abspath(OUTPUT_DIR)}/")
    for f in saved_files:
        print(f"    - {os.path.basename(f)}")
    print("=" * 60)


# ── BONUS: Load and preview the data ──────────────────────────────────────────
def load_and_preview(year=2020):
    """Helper to load and preview a saved year of tick data."""
    filepath = os.path.join(OUTPUT_DIR, f"{SYMBOL}_ticks_{year}.csv")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    print(f"\n📊 Preview of {SYMBOL} tick data for {year}:")
    print(f"   Total trades : {len(df):,}")
    print(f"   Date range   : {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"   Price range  : ${df['price'].min():.2f} → ${df['price'].max():.2f}")
    print(f"\n{df.head(10)}")
    return df


if __name__ == "__main__":
    main()

    # Uncomment to preview after downloading:
    # load_and_preview(year=2020)
