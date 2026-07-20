-- ================================================================
-- 01_schema.sql
-- Star-schema DDL for the Stock Market Portfolio Analytics project.
-- Designed for SQLite (matches your retail sales project setup) but
-- runs on Postgres/MySQL with minor type tweaks (see comments).
-- ================================================================

DROP TABLE IF EXISTS fact_prices;
DROP TABLE IF EXISTS fact_metrics;
DROP TABLE IF EXISTS fact_portfolio;
DROP TABLE IF EXISTS fact_correlation;
DROP TABLE IF EXISTS dim_stock;

CREATE TABLE dim_stock (
    Ticker      TEXT PRIMARY KEY,
    Sector      TEXT NOT NULL,
    CompanyName TEXT NOT NULL
);

CREATE TABLE fact_prices (
    Date        TEXT NOT NULL,          -- ISO date, e.g. '2026-07-18'
    Ticker      TEXT NOT NULL,
    Sector      TEXT NOT NULL,
    Close       REAL,
    AdjClose    REAL,                   -- maps to "Adj Close" column in CSV
    Volume      INTEGER,
    DailyReturn REAL,
    FOREIGN KEY (Ticker) REFERENCES dim_stock (Ticker)
);

CREATE TABLE fact_metrics (
    Ticker                  TEXT PRIMARY KEY,   -- includes 'EQUAL_WEIGHT_PORTFOLIO' row
    Sector                  TEXT NOT NULL,
    AnnualizedReturn        REAL,
    AnnualizedVolatility    REAL,
    SharpeRatio             REAL,
    Beta                    REAL,
    Alpha                   REAL,
    VaR_95_Daily            REAL,
    VaR_99_Daily            REAL,
    CVaR_95_Daily           REAL,
    MaxDrawdown             REAL,
    MaxDrawdownDurationDays INTEGER
);

CREATE TABLE fact_portfolio (
    Date                TEXT NOT NULL PRIMARY KEY,
    PortfolioCumReturn  REAL,
    BenchmarkCumReturn  REAL
);

CREATE TABLE fact_correlation (
    TickerA     TEXT NOT NULL,
    TickerB     TEXT NOT NULL,
    Correlation REAL,
    PRIMARY KEY (TickerA, TickerB)
);

CREATE INDEX idx_fact_prices_ticker ON fact_prices (Ticker);
CREATE INDEX idx_fact_prices_date   ON fact_prices (Date);

-- ================================================================
-- Loading data (SQLite CLI, run from the project root):
--
--   sqlite3 outputs/stock_portfolio.db
--   .mode csv
--   .import powerbi/dim_stock.csv dim_stock_import
--   -- (repeat .import for each table into a staging table, then
--   --  INSERT INTO ... SELECT ... to cast types, since .import
--   --  brings everything in as TEXT by default)
--
-- Simpler alternative: load the CSVs directly with pandas.to_sql()
-- from a small Python snippet -- see scripts/06_load_to_sqlite.py
-- ================================================================
