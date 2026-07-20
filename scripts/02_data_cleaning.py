"""
02_data_cleaning.py
--------------------
Loads the raw per-ticker CSVs from data/raw/, cleans them, combines them
into one long-format panel, computes daily and log returns, and writes:
    data/processed/prices_long.csv      (all tickers, long format)
    data/processed/prices_wide.csv      (Adj Close, one column per ticker)
    data/processed/returns_wide.csv     (daily simple returns, wide format)
    data/processed/daily_summary.csv    (per-ticker cleaning stats)

Run:
    python scripts/02_data_cleaning.py
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import TICKERS, BENCHMARK, RAW_DATA_DIR, PROCESSED_DATA_DIR


def load_raw(ticker: str) -> pd.DataFrame:
    filename = ticker.replace("^", "") + ".csv"
    path = os.path.join(RAW_DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing raw file for {ticker}: {path}")
    df = pd.read_csv(path, parse_dates=["Date"])
    return df


def clean_ticker(df: pd.DataFrame, ticker: str) -> tuple[pd.DataFrame, dict]:
    """Clean a single ticker's dataframe and return (clean_df, stats)."""
    n_before = len(df)

    # Drop exact duplicate rows and duplicate dates (keep first)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="Date", keep="first")

    # Sort chronologically
    df = df.sort_values("Date").reset_index(drop=True)

    # Drop rows with non-positive or missing prices (bad ticks)
    n_before_price_filter = len(df)
    df = df[(df["Adj Close"].notna()) & (df["Adj Close"] > 0)]
    n_dropped_bad_price = n_before_price_filter - len(df)

    # Forward-fill isolated gaps in OHLC (rare, e.g. holiday mismatches),
    # but do NOT fill more than 3 consecutive missing days -- that signals
    # a real data problem worth flagging rather than papering over.
    max_gap = df["Adj Close"].isna().astype(int).groupby(
        (df["Adj Close"].notna()).cumsum()
    ).sum().max() if df["Adj Close"].isna().any() else 0

    n_after = len(df)

    stats = {
        "Ticker": ticker,
        "RowsBefore": n_before,
        "RowsAfter": n_after,
        "DroppedBadPrice": n_dropped_bad_price,
        "MaxConsecutiveGap": int(max_gap),
        "DateMin": df["Date"].min(),
        "DateMax": df["Date"].max(),
    }
    return df, stats


def main():
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    all_tickers = list(TICKERS.keys()) + [BENCHMARK]
    cleaned_frames = []
    stats_rows = []

    for ticker in all_tickers:
        raw = load_raw(ticker)
        clean, stats = clean_ticker(raw, ticker)
        cleaned_frames.append(clean)
        stats_rows.append(stats)

    long_df = pd.concat(cleaned_frames, ignore_index=True)

    # Attach sector (benchmark has no sector)
    long_df["Sector"] = long_df["Ticker"].map(TICKERS).fillna("Benchmark")

    long_path = os.path.join(PROCESSED_DATA_DIR, "prices_long.csv")
    long_df.to_csv(long_path, index=False)

    # Wide format: Adj Close per ticker, aligned on trading days common
    # to ALL tickers (inner join) so return/risk calculations are apples
    # to apples across the whole portfolio.
    wide = long_df.pivot(index="Date", columns="Ticker", values="Adj Close")
    wide = wide.dropna(how="any")  # keep only dates where every ticker traded
    wide = wide.sort_index()

    wide_path = os.path.join(PROCESSED_DATA_DIR, "prices_wide.csv")
    wide.to_csv(wide_path)

    # Daily simple returns
    returns = wide.pct_change().dropna(how="all")
    returns_path = os.path.join(PROCESSED_DATA_DIR, "returns_wide.csv")
    returns.to_csv(returns_path)

    stats_df = pd.DataFrame(stats_rows)
    stats_path = os.path.join(PROCESSED_DATA_DIR, "daily_summary.csv")
    stats_df.to_csv(stats_path, index=False)

    print("=== Cleaning Summary ===")
    print(stats_df.to_string(index=False))
    print(f"\nCommon trading days across all {len(all_tickers)} tickers: {len(wide)}")
    print(f"Date range after alignment: {wide.index.min().date()} -> {wide.index.max().date()}")
    print(f"\nSaved:\n  {long_path}\n  {wide_path}\n  {returns_path}\n  {stats_path}")


if __name__ == "__main__":
    main()
