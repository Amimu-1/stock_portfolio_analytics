"""
config.py
Central configuration for the Stock Market Portfolio Analytics project.
Edit this file to change the stock universe, date range, or risk-free rate.
"""

# ---------------------------------------------------------------
# Stock universe: 15 major US stocks across 5 sectors
# ---------------------------------------------------------------
TICKERS = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "NVDA": "Technology",
    "JPM":  "Financials",
    "BAC":  "Financials",
    "GS":   "Financials",
    "JNJ":  "Healthcare",
    "UNH":  "Healthcare",
    "PFE":  "Healthcare",
    "AMZN": "Consumer",
    "WMT":  "Consumer",
    "PG":   "Consumer",
    "XOM":  "Energy",
    "CVX":  "Energy",
}

BENCHMARK = "^GSPC"  # S&P 500 index, used for Beta / Alpha calculations

# ---------------------------------------------------------------
# Date range for historical data
# ---------------------------------------------------------------
START_DATE = "2021-01-01"
END_DATE = "2026-07-18"   # update to "today" if you want the latest close

# ---------------------------------------------------------------
# Risk-free rate (annualized), used in Sharpe Ratio and Alpha
# 4.5% approximates recent short-term US Treasury yields.
# Edit this if you want to pull the live 13-week T-bill (^IRX) instead.
# ---------------------------------------------------------------
RISK_FREE_RATE_ANNUAL = 0.045

TRADING_DAYS_PER_YEAR = 252

# ---------------------------------------------------------------
# Paths
# ---------------------------------------------------------------
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
OUTPUTS_DIR = "outputs"
