# Power BI Dashboard Build Guide

Step-by-step instructions to build the 4-page dashboard from the CSVs in
this folder. Written for Power BI Desktop.

## 1. Import the data

**Get Data → Text/CSV**, import each of these five files:

- `dim_stock.csv`
- `fact_prices.csv`
- `fact_metrics.csv`
- `fact_portfolio.csv`
- `fact_correlation.csv`

## 2. Set data types

In Power Query, before loading:
- `fact_prices.Date` and `fact_portfolio.Date` → **Date**
- All numeric columns (`Close`, `AdjClose`, `DailyReturn`, `SharpeRatio`,
  `Beta`, `Alpha`, `VaR_95_Daily`, etc.) → **Decimal Number**
- `Volume`, `MaxDrawdownDurationDays` → **Whole Number**

## 3. Build relationships (Model view)

- `dim_stock[Ticker]` (1) → `fact_prices[Ticker]` (many)
- `dim_stock[Ticker]` (1) → `fact_metrics[Ticker]` (many) — *Note: `fact_metrics`
  has one extra row, `EQUAL_WEIGHT_PORTFOLIO`, that won't match `dim_stock`.
  That's expected — it powers the portfolio KPI cards on Page 1 directly
  from `fact_metrics`, not through the relationship.*
- `fact_correlation[TickerA]` → `dim_stock[Ticker]` (inactive relationship is fine;
  the correlation matrix visual uses `TickerA`/`TickerB` directly as matrix axes)

## 4. Core DAX measures

Create these in a new table (Modeling → New Table → name it `_Measures`)
or directly on `fact_metrics`:

```dax
Portfolio Return =
CALCULATE(
    SELECTEDVALUE(fact_metrics[AnnualizedReturn]),
    fact_metrics[Ticker] = "EQUAL_WEIGHT_PORTFOLIO"
)

Portfolio Volatility =
CALCULATE(
    SELECTEDVALUE(fact_metrics[AnnualizedVolatility]),
    fact_metrics[Ticker] = "EQUAL_WEIGHT_PORTFOLIO"
)

Portfolio Sharpe =
CALCULATE(
    SELECTEDVALUE(fact_metrics[SharpeRatio]),
    fact_metrics[Ticker] = "EQUAL_WEIGHT_PORTFOLIO"
)

Portfolio Max Drawdown =
CALCULATE(
    SELECTEDVALUE(fact_metrics[MaxDrawdown]),
    fact_metrics[Ticker] = "EQUAL_WEIGHT_PORTFOLIO"
)

Avg Stock Sharpe (ex-portfolio) =
CALCULATE(
    AVERAGE(fact_metrics[SharpeRatio]),
    fact_metrics[Ticker] <> "EQUAL_WEIGHT_PORTFOLIO"
)
```

Format `Portfolio Return`, `Portfolio Volatility`, and `Portfolio Max
Drawdown` as **Percentage**; `Portfolio Sharpe` as a plain decimal (2 dp).

## 5. Page-by-page build

### Page 1 — Portfolio Overview
- 4 **Card** visuals: `Portfolio Return`, `Portfolio Volatility`,
  `Portfolio Sharpe`, `Portfolio Max Drawdown`
- **Line chart**: `fact_portfolio[Date]` on X, `PortfolioCumReturn` and
  `BenchmarkCumReturn` both on Y — this is the "growth of $1" chart
- **Donut chart**: `dim_stock[Sector]` by count of `Ticker` — sector
  allocation of the 15-stock universe

### Page 2 — Risk & Return by Stock
- **Scatter chart**: `AnnualizedVolatility` (X) vs. `AnnualizedReturn` (Y),
  bubble size = `SharpeRatio`, legend = `Sector`, details = `Ticker`
  (filter `fact_metrics[Ticker] <> "EQUAL_WEIGHT_PORTFOLIO"` in the visual)
- **Table**: Ticker, Sector, AnnualizedReturn, AnnualizedVolatility,
  SharpeRatio, Beta, Alpha — sortable, conditional formatting (data bars)
  on SharpeRatio
- **Slicer**: `Sector`

### Page 3 — Value at Risk & Drawdown
- **Clustered bar chart**: Ticker on Y, `VaR_95_Daily` and `VaR_99_Daily`
  on X (side by side) — sort descending by VaR_99
- **Bar chart**: Ticker ranked by `MaxDrawdown` (most negative at top)
- **Table**: Ticker, MaxDrawdown, MaxDrawdownDurationDays, CVaR_95_Daily

### Page 4 — Correlation & Diversification
- **Matrix visual**: Rows = `TickerA`, Columns = `TickerB`, Values =
  `Correlation` — apply a diverging color scale (red-white-green,
  centered at 0) via conditional formatting on the Correlation field
- **Table**: top 10 most-correlated and top 10 least-correlated pairs
  (filter `fact_correlation[TickerA] < fact_correlation[TickerB]` to
  remove symmetric duplicates, then sort)
- **Card**: average pairwise correlation across the universe (a simple
  proxy for how diversified the portfolio actually is)

## 6. Save

Save as `stock_portfolio_dashboard.pbix` in this `powerbi/` folder before
committing to GitHub (GitHub renders a preview thumbnail of .pbix files
but won't let visitors interact with it — mention this in your README
and, if possible, also export each page as a static PNG for the repo).
