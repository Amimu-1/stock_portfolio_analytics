"""
05_powerbi_export.py
---------------------
Builds the final, Power-BI-ready tables. Power BI works best with clean,
flat, well-typed tables rather than the analysis-oriented wide frames used
internally, so this script reshapes everything into a simple star-schema:

    powerbi/fact_prices.csv        (Date, Ticker, Sector, Close, Volume, DailyReturn)
    powerbi/dim_stock.csv          (Ticker, Sector, CompanyName)
    powerbi/fact_metrics.csv       (Ticker, Sector, all risk/return metrics)
    powerbi/fact_portfolio.csv     (Date, PortfolioCumReturn, BenchmarkCumReturn)
    powerbi/fact_correlation.csv   (TickerA, TickerB, Correlation) -- long format,
                                    since Power BI matrix visuals want long data

Run:
    python scripts/05_powerbi_export.py
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import TICKERS, PROCESSED_DATA_DIR

POWERBI_DIR = "powerbi"

# Friendly company names for the dimension table (used in dashboard labels)
COMPANY_NAMES = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc.",
    "NVDA": "NVIDIA Corp.", "JPM": "JPMorgan Chase & Co.", "BAC": "Bank of America Corp.",
    "GS": "Goldman Sachs Group Inc.", "JNJ": "Johnson & Johnson", "UNH": "UnitedHealth Group Inc.",
    "PFE": "Pfizer Inc.", "AMZN": "Amazon.com Inc.", "WMT": "Walmart Inc.",
    "PG": "Procter & Gamble Co.", "XOM": "Exxon Mobil Corp.", "CVX": "Chevron Corp.",
}


def main():
    os.makedirs(POWERBI_DIR, exist_ok=True)

    long_prices = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "prices_long.csv"),
                               parse_dates=["Date"])
    returns_wide = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "returns_wide.csv"),
                                index_col="Date", parse_dates=True)
    stock_metrics = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "stock_metrics.csv"))
    portfolio_metrics = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "portfolio_metrics.csv"))
    cum_returns = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "portfolio_cum_returns.csv"),
                               parse_dates=["Date"])
    corr = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "correlation_matrix.csv"), index_col=0)

    # ---------------------------------------------------------------
    # dim_stock
    # ---------------------------------------------------------------
    dim_stock = pd.DataFrame({
        "Ticker": list(TICKERS.keys()),
        "Sector": [TICKERS[t] for t in TICKERS.keys()],
        "CompanyName": [COMPANY_NAMES.get(t, t) for t in TICKERS.keys()],
    })
    dim_stock.to_csv(os.path.join(POWERBI_DIR, "dim_stock.csv"), index=False)

    # ---------------------------------------------------------------
    # fact_prices (long format, only the 15 stocks, not the benchmark,
    # since the benchmark is used for metrics, not per-stock browsing)
    # ---------------------------------------------------------------
    fact_prices = long_prices[long_prices["Ticker"].isin(TICKERS.keys())].copy()
    fact_prices = fact_prices[["Date", "Ticker", "Sector", "Close", "Adj Close", "Volume"]]

    returns_long = returns_wide[list(TICKERS.keys())].reset_index().melt(
        id_vars="Date", var_name="Ticker", value_name="DailyReturn")
    fact_prices = fact_prices.merge(returns_long, on=["Date", "Ticker"], how="left")
    fact_prices.to_csv(os.path.join(POWERBI_DIR, "fact_prices.csv"), index=False)

    # ---------------------------------------------------------------
    # fact_metrics (stocks + portfolio row, so Power BI can compare
    # any single stock against the blended portfolio in one table)
    # ---------------------------------------------------------------
    portfolio_metrics = portfolio_metrics.rename(columns={"Unnamed: 0": "Ticker"})
    portfolio_metrics["Sector"] = "Portfolio"
    fact_metrics = pd.concat([stock_metrics, portfolio_metrics], ignore_index=True)
    fact_metrics.to_csv(os.path.join(POWERBI_DIR, "fact_metrics.csv"), index=False)

    # ---------------------------------------------------------------
    # fact_portfolio (time series for the growth-of-$1 chart)
    # ---------------------------------------------------------------
    cum_returns.to_csv(os.path.join(POWERBI_DIR, "fact_portfolio.csv"), index=False)

    # ---------------------------------------------------------------
    # fact_correlation (long format for a Power BI matrix/heatmap visual)
    # ---------------------------------------------------------------
    corr_long = corr.reset_index().melt(id_vars="index", var_name="TickerB", value_name="Correlation")
    corr_long = corr_long.rename(columns={"index": "TickerA"})
    corr_long.to_csv(os.path.join(POWERBI_DIR, "fact_correlation.csv"), index=False)

    print("=== Power BI Export Complete ===")
    for f in ["dim_stock.csv", "fact_prices.csv", "fact_metrics.csv",
              "fact_portfolio.csv", "fact_correlation.csv"]:
        path = os.path.join(POWERBI_DIR, f)
        df = pd.read_csv(path)
        print(f"  {f}: {df.shape[0]} rows x {df.shape[1]} cols")
    print(f"\nAll files saved to {POWERBI_DIR}/ -- ready to import into Power BI Desktop.")


if __name__ == "__main__":
    main()
