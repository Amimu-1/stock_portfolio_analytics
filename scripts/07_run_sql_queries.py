"""
07_run_sql_queries.py
-----------------------
Runs every query in sql/02_analysis_queries.sql against
outputs/stock_portfolio.db, prints the results to the console, and saves
them all to outputs/sql_query_results.txt for easy reference.

Run:
    python scripts/07_run_sql_queries.py
"""

import sqlite3
import pandas as pd

DB_PATH = "outputs/stock_portfolio.db"
SQL_PATH = "sql/02_analysis_queries.sql"
RESULTS_PATH = "outputs/sql_query_results.txt"


def split_statements(sql_text: str):
    """Split the .sql file into individual runnable statements, skipping comments."""
    statements = []
    current = []
    for line in sql_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--") or stripped == "":
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current))
            current = []
    return statements


def main():
    conn = sqlite3.connect(DB_PATH)
    sql_text = open(SQL_PATH, encoding="utf-8").read()
    statements = split_statements(sql_text)

    output_lines = []
    print(f"Running {len(statements)} queries from {SQL_PATH}...\n")

    for i, stmt in enumerate(statements, 1):
        header = f"\n{'='*70}\nQuery {i}\n{'='*70}"
        print(header)
        output_lines.append(header)
        try:
            df = pd.read_sql_query(stmt, conn)
            text = df.to_string(index=False)
            print(text)
            output_lines.append(text)
        except Exception as e:
            err = f"FAILED: {e}"
            print(err)
            output_lines.append(err)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    conn.close()
    print(f"\n\nAll results also saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
