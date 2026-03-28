# Data Downloader

Tick-by-tick historical trade data downloader using the [Alpaca Markets API](https://alpaca.markets). Downloads all trades for a given stock symbol and saves them to CSV files split by year.

## Features

- Downloads tick-level trade data from Alpaca's IEX feed (free tier)
- Handles pagination and rate limiting automatically
- Splits output into per-year CSV files
- Skips years that have already been downloaded
- Includes a preview helper to inspect downloaded data

## Setup

1. Sign up for a free account at [Alpaca Markets](https://alpaca.markets)
2. Get your API keys from the dashboard
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Open `main.py` and set your `API_KEY` and `API_SECRET`

## Configuration

Edit the config section at the top of `main.py`:

| Variable | Description | Default |
|---|---|---|
| `SYMBOL` | Stock ticker to download | `UNH` |
| `START_DATE` | Start of date range | `2020-01-01` |
| `END_DATE` | End of date range | `2024-12-31` |
| `OUTPUT_DIR` | Directory for CSV output | `./unh_tick_data` |

## Usage

```bash
python main.py
```

Output CSVs contain the following columns: `timestamp`, `price`, `size`, `exchange`, `trade_id`, `conditions`, `tape`.
