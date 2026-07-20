"""
03_metrics_calculation.py
--------------------------
Computes the core risk/return metrics for every stock (and an equal-weight
portfolio) using the cleaned returns from data/processed/returns_wide.csv:

    - Annualized Return
    - Annualized Volatility
    - Sharpe Ratio
    - Beta        (vs S&P 500)
    - Alpha       (annualized, CAPM-based, vs S&P 500)
    - Value at Risk (95% and 99%, historical method, daily)
    - Conditional VaR / Expected Shortfall (95%)
    - Maximum Drawdown
    - Max Drawdown Duration (trading days)

Outputs:
    data/processed/stock_metrics.csv        (one row per ticker)
    data/processed/portfolio_metrics.csv    (one row: equal-weight portfolio)
    data/processed/portfolio_cum_returns.csv (cumulative return series, for charting)

Run:
    python scripts/03_metrics_calculation.py
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    TICKERS, BENCHMARK, PROCESSED_DATA_DIR,
    RISK_FREE_RATE_ANNUAL, TRADING_DAYS_PER_YEAR,
)


def annualized_return(daily_returns: pd.Series, periods_per_year: int) -> float:
    growth = (1 + daily_returns).prod()
    n_years = len(daily_returns) / periods_per_year
    if n_years <= 0 or growth <= 0:
        return np.nan
    return growth ** (1 / n_years) - 1


def annualized_volatility(daily_returns: pd.Series, periods_per_year: int) -> float:
    return daily_returns.std() * np.sqrt(periods_per_year)


def sharpe_ratio(daily_returns: pd.Series, rf_annual: float, periods_per_year: int) -> float:
    rf_daily = (1 + rf_annual) ** (1 / periods_per_year) - 1
    excess = daily_returns - rf_daily
    if excess.std() == 0:
        return np.nan
    return (excess.mean() / excess.std()) * np.sqrt(periods_per_year)


def beta_alpha(asset_returns: pd.Series, market_returns: pd.Series,
                rf_annual: float, periods_per_year: int) -> tuple[float, float]:
    """CAPM beta and annualized alpha vs the market (benchmark)."""
    aligned = pd.concat([asset_returns, market_returns], axis=1).dropna()
    aligned.columns = ["asset", "market"]
    if len(aligned) < 2 or aligned["market"].var() == 0:
        return np.nan, np.nan

    cov = np.cov(aligned["asset"], aligned["market"])[0, 1]
    var_market = np.var(aligned["market"], ddof=1)
    beta = cov / var_market

    rf_daily = (1 + rf_annual) ** (1 / periods_per_year) - 1
    asset_ann_return = annualized_return(aligned["asset"], periods_per_year)
    market_ann_return = annualized_return(aligned["market"], periods_per_year)
    alpha = asset_ann_return - (rf_annual + beta * (market_ann_return - rf_annual))
    return beta, alpha


def historical_var(daily_returns: pd.Series, confidence: float) -> float:
    """Historical VaR as a positive number representing a loss (e.g. 0.025 = 2.5% daily loss)."""
    return -np.percentile(daily_returns.dropna(), (1 - confidence) * 100)


def conditional_var(daily_returns: pd.Series, confidence: float) -> float:
    """Expected shortfall: average loss beyond the VaR threshold."""
    var = historical_var(daily_returns, confidence)
    tail_losses = daily_returns[daily_returns <= -var]
    if len(tail_losses) == 0:
        return var
    return -tail_losses.mean()


def max_drawdown(daily_returns: pd.Series) -> tuple[float, int]:
    """Returns (max_drawdown as negative fraction, duration in trading days)."""
    cum = (1 + daily_returns).cumprod()
    running_max = cum.cummax()
    drawdown = cum / running_max - 1
    mdd = drawdown.min()

    # duration: longest streak the series stayed below its prior peak
    underwater = drawdown < 0
    if not underwater.any():
        return 0.0, 0
    # group consecutive True values
    groups = (~underwater).cumsum()
    durations = underwater.groupby(groups).sum()
    max_duration = int(durations.max())
    return float(mdd), max_duration


def compute_metrics_for_series(returns: pd.Series, market_returns: pd.Series) -> dict:
    ann_ret = annualized_return(returns, TRADING_DAYS_PER_YEAR)
    ann_vol = annualized_volatility(returns, TRADING_DAYS_PER_YEAR)
    sharpe = sharpe_ratio(returns, RISK_FREE_RATE_ANNUAL, TRADING_DAYS_PER_YEAR)
    beta, alpha = beta_alpha(returns, market_returns, RISK_FREE_RATE_ANNUAL, TRADING_DAYS_PER_YEAR)
    var_95 = historical_var(returns, 0.95)
    var_99 = historical_var(returns, 0.99)
    cvar_95 = conditional_var(returns, 0.95)
    mdd, mdd_duration = max_drawdown(returns)

    return {
        "AnnualizedReturn": ann_ret,
        "AnnualizedVolatility": ann_vol,
        "SharpeRatio": sharpe,
        "Beta": beta,
        "Alpha": alpha,
        "VaR_95_Daily": var_95,
        "VaR_99_Daily": var_99,
        "CVaR_95_Daily": cvar_95,
        "MaxDrawdown": mdd,
        "MaxDrawdownDurationDays": mdd_duration,
    }


def main():
    returns_path = os.path.join(PROCESSED_DATA_DIR, "returns_wide.csv")
    returns = pd.read_csv(returns_path, index_col="Date", parse_dates=True)

    benchmark_col = BENCHMARK  # e.g. "^GSPC"
    if benchmark_col not in returns.columns:
        raise ValueError(f"Benchmark {benchmark_col} not found in returns columns: {list(returns.columns)}")

    market_returns = returns[benchmark_col]

    rows = []
    for ticker in TICKERS.keys():
        if ticker not in returns.columns:
            print(f"⚠ Skipping {ticker}: not found in returns data")
            continue
        m = compute_metrics_for_series(returns[ticker], market_returns)
        m["Ticker"] = ticker
        m["Sector"] = TICKERS[ticker]
        rows.append(m)

    stock_metrics = pd.DataFrame(rows).set_index("Ticker")
    col_order = ["Sector", "AnnualizedReturn", "AnnualizedVolatility", "SharpeRatio",
                 "Beta", "Alpha", "VaR_95_Daily", "VaR_99_Daily", "CVaR_95_Daily",
                 "MaxDrawdown", "MaxDrawdownDurationDays"]
    stock_metrics = stock_metrics[col_order]
    stock_metrics_path = os.path.join(PROCESSED_DATA_DIR, "stock_metrics.csv")
    stock_metrics.to_csv(stock_metrics_path)

    # Equal-weight portfolio
    tickers_in_data = [t for t in TICKERS if t in returns.columns]
    port_returns = returns[tickers_in_data].mean(axis=1)
    port_metrics = compute_metrics_for_series(port_returns, market_returns)
    port_metrics_df = pd.DataFrame([port_metrics], index=["EQUAL_WEIGHT_PORTFOLIO"])
    port_metrics_path = os.path.join(PROCESSED_DATA_DIR, "portfolio_metrics.csv")
    port_metrics_df.to_csv(port_metrics_path)

    # Cumulative return series for charting (portfolio vs benchmark)
    cum_portfolio = (1 + port_returns).cumprod()
    cum_benchmark = (1 + market_returns.reindex(port_returns.index)).cumprod()
    cum_df = pd.DataFrame({
        "PortfolioCumReturn": cum_portfolio,
        "BenchmarkCumReturn": cum_benchmark,
    })
    cum_path = os.path.join(PROCESSED_DATA_DIR, "portfolio_cum_returns.csv")
    cum_df.to_csv(cum_path)

    print("=== Stock-Level Metrics ===")
    print(stock_metrics.round(4).to_string())
    print("\n=== Equal-Weight Portfolio Metrics ===")
    print(port_metrics_df.round(4).to_string())
    print(f"\nSaved:\n  {stock_metrics_path}\n  {port_metrics_path}\n  {cum_path}")


if __name__ == "__main__":
    main()
