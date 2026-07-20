-- ================================================================
-- 02_analysis_queries.sql
-- Analytical queries for the Stock Market Portfolio Analytics project.
-- Run against outputs/stock_portfolio.db (built by scripts/06_load_to_sqlite.py)
-- Tested on SQLite; window functions also work unchanged on Postgres/MySQL 8+.
-- ================================================================

-- ----------------------------------------------------------------
-- Q1. Risk-adjusted leaderboard: rank every stock by Sharpe Ratio
--     within its own sector using a window function.
-- ----------------------------------------------------------------
SELECT
    Ticker,
    Sector,
    ROUND(AnnualizedReturn, 4)     AS AnnualizedReturn,
    ROUND(SharpeRatio, 4)          AS SharpeRatio,
    RANK() OVER (PARTITION BY Sector ORDER BY SharpeRatio DESC) AS SectorSharpeRank
FROM fact_metrics
WHERE Ticker <> 'EQUAL_WEIGHT_PORTFOLIO'
ORDER BY Sector, SectorSharpeRank;


-- ----------------------------------------------------------------
-- Q2. Sector-level risk/return summary, with each sector's share of
--     total portfolio "risk budget" (sum of volatility as a proxy).
-- ----------------------------------------------------------------
SELECT
    Sector,
    COUNT(*)                                   AS NumStocks,
    ROUND(AVG(AnnualizedReturn), 4)            AS AvgAnnualizedReturn,
    ROUND(AVG(AnnualizedVolatility), 4)        AS AvgAnnualizedVolatility,
    ROUND(AVG(SharpeRatio), 4)                 AS AvgSharpeRatio,
    ROUND(SUM(AnnualizedVolatility) * 100.0 /
        (SELECT SUM(AnnualizedVolatility) FROM fact_metrics WHERE Ticker <> 'EQUAL_WEIGHT_PORTFOLIO'), 2)
                                                AS PctOfTotalVolatility
FROM fact_metrics
WHERE Ticker <> 'EQUAL_WEIGHT_PORTFOLIO'
GROUP BY Sector
ORDER BY AvgSharpeRatio DESC;


-- ----------------------------------------------------------------
-- Q3. Which stocks beat the equal-weight portfolio on a risk-adjusted
--     basis (higher Sharpe) AND carry lower drawdown risk?
--     ("Best of both worlds" candidates for overweighting.)
-- ----------------------------------------------------------------
WITH portfolio AS (
    SELECT SharpeRatio, MaxDrawdown
    FROM fact_metrics
    WHERE Ticker = 'EQUAL_WEIGHT_PORTFOLIO'
)
SELECT
    m.Ticker,
    m.Sector,
    ROUND(m.SharpeRatio, 4)   AS StockSharpe,
    ROUND(p.SharpeRatio, 4)   AS PortfolioSharpe,
    ROUND(m.MaxDrawdown, 4)  AS StockMaxDrawdown,
    ROUND(p.MaxDrawdown, 4)  AS PortfolioMaxDrawdown
FROM fact_metrics m, portfolio p
WHERE m.Ticker <> 'EQUAL_WEIGHT_PORTFOLIO'
  AND m.SharpeRatio > p.SharpeRatio
  AND m.MaxDrawdown > p.MaxDrawdown   -- less negative = smaller drawdown
ORDER BY m.SharpeRatio DESC;


-- ----------------------------------------------------------------
-- Q4. Rolling 20-day volatility trend for a single stock (parameterize
--     the Ticker filter). Demonstrates window functions over a
--     financial time series.
-- ----------------------------------------------------------------
SELECT
    Date,
    Ticker,
    DailyReturn,
    ROUND(
        (SELECT AVG((r2.DailyReturn - sub.avg_ret) * (r2.DailyReturn - sub.avg_ret))
         FROM fact_prices r2
         WHERE r2.Ticker = fp.Ticker
           AND r2.Date <= fp.Date
           AND r2.Date > DATE(fp.Date, '-28 day')),
    6) AS Rolling20DayVarianceApprox
FROM fact_prices fp,
     (SELECT AVG(DailyReturn) AS avg_ret FROM fact_prices WHERE Ticker = 'AAPL') sub
WHERE fp.Ticker = 'AAPL'
ORDER BY fp.Date;
-- NOTE: SQLite has no native rolling-window frame with dates, so this
-- approximates a 20-trading-day window via a 28-calendar-day lookback.
-- For a cleaner rolling window, use pandas (already computed in Python)
-- or Postgres' native `OVER (ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)`.


-- ----------------------------------------------------------------
-- Q5. Correlation pairs: the 10 most correlated stock pairs (excluding
--     a stock's correlation with itself), useful for spotting
--     diversification gaps.
-- ----------------------------------------------------------------
SELECT
    TickerA,
    TickerB,
    ROUND(Correlation, 3) AS Correlation
FROM fact_correlation
WHERE TickerA < TickerB              -- de-duplicate symmetric pairs
ORDER BY Correlation DESC
LIMIT 10;


-- ----------------------------------------------------------------
-- Q6. The 10 least correlated (most diversifying) stock pairs.
-- ----------------------------------------------------------------
SELECT
    TickerA,
    TickerB,
    ROUND(Correlation, 3) AS Correlation
FROM fact_correlation
WHERE TickerA < TickerB
ORDER BY Correlation ASC
LIMIT 10;


-- ----------------------------------------------------------------
-- Q7. Portfolio vs benchmark: month-over-month growth comparison
--     using LAG() to compute period-over-period % change.
-- ----------------------------------------------------------------
SELECT
    Date,
    ROUND(PortfolioCumReturn, 4)  AS PortfolioCumReturn,
    ROUND(BenchmarkCumReturn, 4)  AS BenchmarkCumReturn,
    ROUND(
        (PortfolioCumReturn - LAG(PortfolioCumReturn) OVER (ORDER BY Date))
        / LAG(PortfolioCumReturn) OVER (ORDER BY Date) * 100, 3
    ) AS PortfolioDailyPctChange
FROM fact_portfolio
ORDER BY Date;


-- ----------------------------------------------------------------
-- Q8. Company + sector lookup joined with metrics (basic join demo,
--     the kind of query a dashboard "stock detail" page would use).
-- ----------------------------------------------------------------
SELECT
    d.Ticker,
    d.CompanyName,
    d.Sector,
    ROUND(m.AnnualizedReturn, 4)  AS AnnualizedReturn,
    ROUND(m.Beta, 3)              AS Beta,
    ROUND(m.VaR_95_Daily, 4)      AS VaR_95_Daily
FROM dim_stock d
JOIN fact_metrics m ON d.Ticker = m.Ticker
ORDER BY m.AnnualizedReturn DESC;
