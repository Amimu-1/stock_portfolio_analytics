# 📈 Stock Market Portfolio Risk & Return Analytics

An end-to-end analytics pipeline that downloads real market data for a
15-stock, 5-sector universe, computes institutional-grade risk and return
metrics (Sharpe Ratio, Beta, Alpha, Value at Risk, Maximum Drawdown), and
surfaces the results through SQL analysis and a 4-page Power BI dashboard.

Built as a portfolio project by **Aminu Momodu Audu** —
[LinkedIn](https://www.linkedin.com/in/aminu-momodu-audu-040359406) ·
[GitHub](https://github.com/Amimu-1)

---

## 🎯 Project Overview

| | |
|---|---|
| **Data source** | [yfinance](https://pypi.org/project/yfinance/) (Yahoo Finance) — real daily OHLCV prices |
| **Universe** | 15 major US stocks across Technology, Financials, Healthcare, Consumer, and Energy, benchmarked against the S&P 500 (`^GSPC`) |
| **Date range** | Jan 2021 – present (configurable in `scripts/config.py`) |
| **Stack** | Python (pandas, numpy, matplotlib, seaborn) → SQL (SQLite) → Power BI |

This project mirrors the structure of my
[Retail Sales Analytics project](https://github.com/Amimu-1/retail_sales_analysis):
raw data → cleaning → metrics/EDA → SQL → BI dashboard, applied here to
quantitative finance instead of retail.

---

## 🧮 Metrics Computed

For every stock and for an equal-weight portfolio, the pipeline computes:

- **Annualized Return** — geometric growth rate, annualized from daily returns
- **Annualized Volatility** — standard deviation of daily returns, annualized
- **Sharpe Ratio** — risk-adjusted return vs. a 4.5% annual risk-free rate
- **Beta** — sensitivity to the S&P 500 (systematic risk)
- **Alpha** — CAPM-based excess return after adjusting for Beta
- **Value at Risk (95% / 99%, historical method)** — the daily loss threshold not expected to be exceeded at each confidence level
- **Conditional VaR / Expected Shortfall (95%)** — the average loss *given* that VaR is breached
- **Maximum Drawdown** — largest peak-to-trough decline, and how long it lasted (trading days)

---

## 📂 Project Structure

```
stock_portfolio_analytics/
├── data/
│   ├── raw/                  # per-ticker CSVs straight from yfinance (gitignored)
│   └── processed/            # cleaned, joined, and metrics tables
├── scripts/
│   ├── config.py                  # stock universe, date range, risk-free rate
│   ├── 01_data_download.py        # pulls OHLCV data via yfinance
│   ├── 02_data_cleaning.py        # dedupes, aligns trading days, computes returns
│   ├── 03_metrics_calculation.py  # Sharpe, Beta, Alpha, VaR, CVaR, Max Drawdown
│   ├── 04_eda.py                  # correlation heatmap, risk/return scatter, etc.
│   ├── 05_powerbi_export.py       # builds the star-schema tables for Power BI
│   └── 06_load_to_sqlite.py       # loads star-schema into SQLite for SQL analysis
├── sql/
│   ├── 01_schema.sql          # star-schema DDL
│   └── 02_analysis_queries.sql # 8 analytical queries (window functions, joins, CTEs)
├── powerbi/                   # star-schema CSVs, ready to import into Power BI
├── outputs/                   # generated charts (.png) and stock_portfolio.db
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run (Windows / Anaconda Prompt)

```bash
# 1. Clone the repo
git clone https://github.com/Amimu-1/stock_portfolio_analytics.git
cd stock_portfolio_analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the pipeline, in order
python scripts/01_data_download.py
python scripts/02_data_cleaning.py
python scripts/03_metrics_calculation.py
python scripts/04_eda.py
python scripts/05_powerbi_export.py
python scripts/06_load_to_sqlite.py
```

Each script prints a summary as it runs, and writes its outputs to
`data/processed/`, `outputs/`, or `powerbi/` so you can inspect results
at every stage of the pipeline.

**Edit `scripts/config.py`** to change the stock list, date range, or
risk-free rate assumption — every downstream script reads from it.

---

## 📊 Power BI Dashboard (4 Pages)

Open Power BI Desktop → **Get Data → Text/CSV** → import all five files
from `powerbi/` (`dim_stock`, `fact_prices`, `fact_metrics`,
`fact_portfolio`, `fact_correlation`) → build relationships on `Ticker`.

| Page | Contents |
|---|---|
| **1. Portfolio Overview** | KPI cards (Portfolio Return, Volatility, Sharpe, Max Drawdown) · Portfolio vs. S&P 500 cumulative growth line chart · Sector allocation donut |
| **2. Risk & Return by Stock** | Risk/return scatter (Volatility vs. Return, bubble = Sharpe) · Sortable table of all 15 stocks' metrics · Sector slicer |
| **3. Value at Risk & Drawdown** | VaR 95%/99% bar chart by stock · Max Drawdown ranked bar chart · Drawdown duration table |
| **4. Correlation & Diversification** | Correlation matrix heatmap (matrix visual on `fact_correlation`) · Most/least correlated pairs table · Sector correlation summary |

*(Full build notes, including exact visual types and DAX measures, are in
`powerbi/DASHBOARD_GUIDE.md`.)*

---

## 🗄️ SQL Analysis

`sql/02_analysis_queries.sql` contains 8 tested queries against the
star schema, including:

- Sector-ranked Sharpe Ratio leaderboard (window function: `RANK() OVER`)
- Sector risk-budget contribution (subquery + aggregation)
- Stocks beating the portfolio on both Sharpe *and* drawdown
- Most/least correlated stock pairs (diversification analysis)
- Portfolio vs. benchmark day-over-day % change (`LAG() OVER`)

Load the data and run them with:

```bash
python scripts/06_load_to_sqlite.py
sqlite3 outputs/stock_portfolio.db < sql/02_analysis_queries.sql
```

---

## 🔍 Key Design Notes

- **Trading-day alignment:** stocks are joined on dates where *all 15*
  tickers traded, so cross-stock comparisons (correlation, portfolio
  returns) are never distorted by mismatched calendars.
- **VaR method:** historical (empirical percentile), not parametric —
  makes no assumption that returns are normally distributed.
- **Risk-free rate:** a fixed 4.5% annual assumption (see
  `scripts/config.py`), documented rather than silently baked in, since
  it directly affects Sharpe Ratio and Alpha.
- **Equal-weight portfolio:** used as the base case for simplicity and
  transparency; the pipeline is structured so a weighting scheme (e.g.
  market-cap or minimum-variance) could be swapped in without touching
  the metrics functions.

---

## 🛠️ Tech Stack

`Python` · `pandas` · `numpy` · `yfinance` · `matplotlib` · `seaborn` ·
`SQLite` · `SQL` (window functions, CTEs) · `Power BI`

---

## 📬 Contact

**Aminu Momodu Audu**
[LinkedIn](https://www.linkedin.com/in/aminu-momodu-audu-040359406) ·
[GitHub](https://github.com/Amimu-1) ·
[Fiverr](https://www.fiverr.com/s/yvKRxkz)
