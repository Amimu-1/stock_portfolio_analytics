"""
04_eda.py
---------
Exploratory data analysis on the cleaned price/return data. Produces:

    outputs/correlation_heatmap.png
    outputs/cumulative_returns.png
    outputs/volatility_by_sector.png
    outputs/risk_return_scatter.png
    outputs/portfolio_vs_benchmark.png
    data/processed/correlation_matrix.csv
    data/processed/sector_summary.csv

Run:
    python scripts/04_eda.py
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless backend, safe for scripts/servers
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import TICKERS, BENCHMARK, PROCESSED_DATA_DIR, OUTPUTS_DIR

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 110


def main():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    returns = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "returns_wide.csv"),
                           index_col="Date", parse_dates=True)
    prices = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "prices_wide.csv"),
                          index_col="Date", parse_dates=True)
    stock_metrics = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "stock_metrics.csv"),
                                 index_col="Ticker")
    cum_returns = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "portfolio_cum_returns.csv"),
                               index_col="Date", parse_dates=True)

    stock_tickers = [t for t in TICKERS if t in returns.columns]

    # ---------------------------------------------------------------
    # 1. Correlation heatmap (stocks only, excludes benchmark)
    # ---------------------------------------------------------------
    corr = returns[stock_tickers].corr()
    corr.to_csv(os.path.join(PROCESSED_DATA_DIR, "correlation_matrix.csv"))

    plt.figure(figsize=(11, 9))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn", center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
    plt.title("Daily Return Correlation Matrix (15 Stocks)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "correlation_heatmap.png"))
    plt.close()

    # ---------------------------------------------------------------
    # 2. Cumulative returns, all stocks
    # ---------------------------------------------------------------
    cum_stocks = (1 + returns[stock_tickers]).cumprod()
    plt.figure(figsize=(13, 7))
    for ticker in stock_tickers:
        plt.plot(cum_stocks.index, cum_stocks[ticker], label=ticker, linewidth=1.3)
    plt.title("Cumulative Returns by Stock", fontsize=14, fontweight="bold")
    plt.ylabel("Growth of $1")
    plt.xlabel("Date")
    plt.legend(ncol=3, fontsize=8, loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "cumulative_returns.png"))
    plt.close()

    # ---------------------------------------------------------------
    # 3. Volatility by sector (boxplot of annualized vol per sector)
    # ---------------------------------------------------------------
    plt.figure(figsize=(9, 6))
    sector_order = stock_metrics.groupby("Sector")["AnnualizedVolatility"].median().sort_values().index
    sns.boxplot(data=stock_metrics.reset_index(), x="Sector", y="AnnualizedVolatility",
                order=sector_order, hue="Sector", palette="Set2", legend=False)
    sns.stripplot(data=stock_metrics.reset_index(), x="Sector", y="AnnualizedVolatility",
                  order=sector_order, color="black", size=6, alpha=0.6)
    plt.title("Annualized Volatility by Sector", fontsize=14, fontweight="bold")
    plt.ylabel("Annualized Volatility")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "volatility_by_sector.png"))
    plt.close()

    sector_summary = stock_metrics.groupby("Sector").agg(
        AvgAnnualizedReturn=("AnnualizedReturn", "mean"),
        AvgAnnualizedVolatility=("AnnualizedVolatility", "mean"),
        AvgSharpeRatio=("SharpeRatio", "mean"),
        AvgBeta=("Beta", "mean"),
        AvgMaxDrawdown=("MaxDrawdown", "mean"),
        NumStocks=("Sector", "count"),
    ).round(4)
    sector_summary.to_csv(os.path.join(PROCESSED_DATA_DIR, "sector_summary.csv"))

    # ---------------------------------------------------------------
    # 4. Risk-return scatter (annualized vol vs annualized return, sized by |Sharpe|)
    # ---------------------------------------------------------------
    plt.figure(figsize=(10, 7))
    sectors = stock_metrics["Sector"].unique()
    palette = sns.color_palette("Set2", len(sectors))
    color_map = dict(zip(sectors, palette))

    for sector in sectors:
        subset = stock_metrics[stock_metrics["Sector"] == sector]
        plt.scatter(subset["AnnualizedVolatility"], subset["AnnualizedReturn"],
                    s=120, label=sector, color=color_map[sector], edgecolor="black", alpha=0.85)
        for ticker, row in subset.iterrows():
            plt.annotate(ticker, (row["AnnualizedVolatility"], row["AnnualizedReturn"]),
                         textcoords="offset points", xytext=(5, 5), fontsize=8)

    plt.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    plt.title("Risk vs Return by Stock", fontsize=14, fontweight="bold")
    plt.xlabel("Annualized Volatility (Risk)")
    plt.ylabel("Annualized Return")
    plt.legend(title="Sector")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "risk_return_scatter.png"))
    plt.close()

    # ---------------------------------------------------------------
    # 5. Portfolio vs benchmark cumulative growth
    # ---------------------------------------------------------------
    plt.figure(figsize=(12, 6))
    plt.plot(cum_returns.index, cum_returns["PortfolioCumReturn"],
              label="Equal-Weight Portfolio", linewidth=2, color="#2E86AB")
    plt.plot(cum_returns.index, cum_returns["BenchmarkCumReturn"],
              label=f"Benchmark ({BENCHMARK})", linewidth=2, color="#A23B72", linestyle="--")
    plt.title("Portfolio vs Benchmark: Cumulative Growth of $1", fontsize=14, fontweight="bold")
    plt.ylabel("Growth of $1")
    plt.xlabel("Date")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "portfolio_vs_benchmark.png"))
    plt.close()

    print("=== EDA Complete ===")
    print("Saved charts to outputs/:")
    for f in ["correlation_heatmap.png", "cumulative_returns.png", "volatility_by_sector.png",
              "risk_return_scatter.png", "portfolio_vs_benchmark.png"]:
        print(f"  - {f}")
    print("\nSector summary:")
    print(sector_summary.to_string())


if __name__ == "__main__":
    main()
