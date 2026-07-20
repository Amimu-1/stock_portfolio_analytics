"""
06_load_to_sqlite.py
----------------------
Loads the Power BI-ready CSVs into a local SQLite database so you can run
the SQL queries in sql/02_analysis_queries.sql (and explore in DB Browser
for SQLite, or via the sqlite3 CLI).

Run:
    python scripts/06_load_to_sqlite.py
"""

import os
import sqlite3
import pandas as pd

POWERBI_DIR = "powerbi"
DB_PATH = "outputs/stock_portfolio.db"


def main():
    os.makedirs("outputs", exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # rebuild fresh each run

    conn = sqlite3.connect(DB_PATH)

    dim_stock = pd.read_csv(os.path.join(POWERBI_DIR, "dim_stock.csv"))
    fact_prices = pd.read_csv(os.path.join(POWERBI_DIR, "fact_prices.csv"))
    fact_prices = fact_prices.rename(columns={"Adj Close": "AdjClose"})
    fact_metrics = pd.read_csv(os.path.join(POWERBI_DIR, "fact_metrics.csv"))
    fact_portfolio = pd.read_csv(os.path.join(POWERBI_DIR, "fact_portfolio.csv"))
    fact_correlation = pd.read_csv(os.path.join(POWERBI_DIR, "fact_correlation.csv"))

    dim_stock.to_sql("dim_stock", conn, if_exists="replace", index=False)
    fact_prices.to_sql("fact_prices", conn, if_exists="replace", index=False)
    fact_metrics.to_sql("fact_metrics", conn, if_exists="replace", index=False)
    fact_portfolio.to_sql("fact_portfolio", conn, if_exists="replace", index=False)
    fact_correlation.to_sql("fact_correlation", conn, if_exists="replace", index=False)

    tables = ["dim_stock", "fact_prices", "fact_metrics", "fact_portfolio", "fact_correlation"]
    print(f"=== Loaded {DB_PATH} ===")
    for t in tables:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} rows")

    conn.close()


if __name__ == "__main__":
    main()
