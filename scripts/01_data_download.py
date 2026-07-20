"""
01_data_download.py
--------------------
Downloads daily OHLCV price history for the 15-stock universe plus the
S&P 500 benchmark using yfinance, and saves one CSV per ticker into
data/raw/.

Run from the project root:
    python -m scripts.01_data_download
(or, since the filename starts with a digit, run it directly:)
    python scripts/01_data_download.py
"""

import os
import sys
import time
import pandas as pd
import yfinance as yf

# allow running this file directly by adding scripts/ to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import TICKERS, BENCHMARK, START_DATE, END_DATE, RAW_DATA_DIR


def download_ticker(ticker: str, start: str, end: str, retries: int = 3) -> pd.DataFrame:
    """Download OHLCV data for one ticker with basic retry logic."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                progress=False,
                auto_adjust=False,  # keep raw Close AND Adj Close separately
            )
            if df is None or df.empty:
                raise ValueError("Empty dataframe returned")
            # yfinance sometimes returns MultiIndex columns for a single ticker
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
            df = df.reset_index()
            # yfinance normally names the index 'Date', but guard against
            # it coming back unnamed (e.g. 'index') so downstream scripts
            # can always rely on a 'Date' column existing.
            first_col = df.columns[0]
            if first_col != "Date":
                df = df.rename(columns={first_col: "Date"})
            df["Ticker"] = ticker
            return df
        except Exception as e:
            last_err = e
            print(f"  attempt {attempt}/{retries} failed for {ticker}: {e}")
            time.sleep(2)
    raise RuntimeError(f"Failed to download {ticker} after {retries} attempts: {last_err}")


def main():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    all_tickers = list(TICKERS.keys()) + [BENCHMARK]
    summary = []

    print(f"Downloading {len(all_tickers)} tickers from {START_DATE} to {END_DATE}...\n")

    for ticker in all_tickers:
        print(f"Downloading {ticker} ...")
        try:
            df = download_ticker(ticker, START_DATE, END_DATE)
            out_path = os.path.join(RAW_DATA_DIR, f"{ticker.replace('^', '')}.csv")
            df.to_csv(out_path, index=False)
            summary.append({
                "Ticker": ticker,
                "Rows": len(df),
                "StartDate": df["Date"].min(),
                "EndDate": df["Date"].max(),
                "Status": "OK",
            })
            print(f"  -> saved {len(df)} rows to {out_path}")
        except Exception as e:
            summary.append({
                "Ticker": ticker, "Rows": 0, "StartDate": None,
                "EndDate": None, "Status": f"FAILED: {e}",
            })
            print(f"  -> FAILED: {e}")

    summary_df = pd.DataFrame(summary)
    summary_path = os.path.join(RAW_DATA_DIR, "_download_summary.csv")
    summary_df.to_csv(summary_path, index=False)

    print("\n=== Download Summary ===")
    print(summary_df.to_string(index=False))

    failed = summary_df[summary_df["Status"] != "OK"]
    if len(failed) > 0:
        print(f"\n⚠ {len(failed)} ticker(s) failed. Check {summary_path} and re-run for those tickers.")
    else:
        print(f"\n✅ All {len(summary_df)} tickers downloaded successfully.")


if __name__ == "__main__":
    main()
