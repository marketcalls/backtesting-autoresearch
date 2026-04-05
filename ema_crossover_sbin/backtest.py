"""
Fixed backtest harness. DO NOT MODIFY.
Loads data, runs the strategy, evaluates metrics, prints summary.
The strategy logic lives in strategy.py — that is the only file the AI agent modifies.

Usage: uv run python ema_crossover_sbin/backtest.py > run.log 2>&1
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import vectorbt as vbt
import yfinance as yf

# --- Config (fixed) ---
SYMBOL = "SBIN.NS"
BENCHMARK_TICKER = "^NSEI"
INIT_CASH = 1_000_000
FEES = 0.00111              # Indian delivery equity (STT + statutory)
FIXED_FEES = 20             # Rs 20 per order
YEARS = 15

script_dir = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)


def load_data():
    """Fetch SBIN and NIFTY data. Returns (df, df_bench)."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365 * YEARS)).strftime("%Y-%m-%d")

    log.info(f"Fetching {SYMBOL} from {start_date} to {end_date}")
    df = yf.download(SYMBOL, start=start_date, end=end_date,
                     interval="1d", auto_adjust=True, multi_level_index=False)
    df.columns = df.columns.str.lower()
    df = df.sort_index()
    if df.index.tz is not None:
        df.index = df.index.tz_convert(None)

    log.info(f"Fetching benchmark {BENCHMARK_TICKER}")
    df_bench = yf.download(BENCHMARK_TICKER, start=start_date, end=end_date,
                           interval="1d", auto_adjust=True, multi_level_index=False)
    df_bench.columns = df_bench.columns.str.lower()
    df_bench = df_bench.sort_index()
    if df_bench.index.tz is not None:
        df_bench.index = df_bench.index.tz_convert(None)

    log.info(f"Loaded {len(df)} bars from {df.index[0].date()} to {df.index[-1].date()}")
    return df, df_bench


def run_backtest(df, entries, exits, allocation=0.95):
    """Run vectorbt backtest with Indian market fees. Returns Portfolio."""
    close = df["close"]
    pf = vbt.Portfolio.from_signals(
        close, entries, exits,
        init_cash=INIT_CASH, size=allocation, size_type="percent",
        fees=FEES, fixed_fees=FIXED_FEES, direction="longonly",
        min_size=1, size_granularity=1, freq="1D",
    )
    return pf


def run_benchmark(df, df_bench):
    """Run buy-and-hold benchmark on NIFTY. Returns Portfolio."""
    close = df["close"]
    bench_close = df_bench["close"].reindex(close.index).ffill().bfill()
    pf_bench = vbt.Portfolio.from_holding(bench_close, init_cash=INIT_CASH, fees=FEES, freq="1D")
    return pf_bench


def compute_score(pf):
    """
    Composite score combining CAGR, Sharpe, and MaxDD.
    Higher is better. This is the metric the AI agent optimizes.

    score = (CAGR% * 0.4) + (Sharpe * 10 * 0.3) + ((100 - MaxDD%) * 0.3)

    Weights:
      - 40% CAGR: reward absolute returns
      - 30% Sharpe: reward risk-adjusted returns
      - 30% (100 - MaxDD%): reward capital preservation
    """
    cagr = pf.annualized_return() * 100
    sharpe = pf.sharpe_ratio()
    max_dd = pf.max_drawdown() * 100  # already negative-signed

    score = (cagr * 0.4) + (sharpe * 10 * 0.3) + ((100 - abs(max_dd)) * 0.3)
    return round(score, 4)


def print_results(pf, pf_bench, score):
    """Print the standardized result summary to stdout."""
    print("\n--- Strategy vs Benchmark ---")
    comparison = pd.DataFrame({
        "Strategy": [
            f"Rs {pf.final_value():,.0f}",
            f"{pf.total_return() * 100:.2f}%",
            f"{pf.annualized_return() * 100:.2f}%",
            f"{pf.sharpe_ratio():.2f}",
            f"{pf.sortino_ratio():.2f}",
            f"{pf.max_drawdown() * 100:.2f}%",
            f"{pf.trades.win_rate() * 100:.1f}%",
            f"{pf.trades.count()}",
            f"{pf.trades.profit_factor():.2f}",
        ],
        f"Benchmark (NIFTY)": [
            f"Rs {pf_bench.final_value():,.0f}",
            f"{pf_bench.total_return() * 100:.2f}%",
            f"{pf_bench.annualized_return() * 100:.2f}%",
            f"{pf_bench.sharpe_ratio():.2f}",
            f"{pf_bench.sortino_ratio():.2f}",
            f"{pf_bench.max_drawdown() * 100:.2f}%",
            "-", "-", "-",
        ],
    }, index=["Final Value", "Total Return", "CAGR", "Sharpe Ratio", "Sortino Ratio",
              "Max Drawdown", "Win Rate", "Total Trades", "Profit Factor"])
    print(comparison.to_string())

    # Machine-readable output block (for grep extraction)
    print("\n---")
    print(f"score:          {score}")
    print(f"cagr:           {pf.annualized_return() * 100:.4f}")
    print(f"sharpe:         {pf.sharpe_ratio():.4f}")
    print(f"sortino:        {pf.sortino_ratio():.4f}")
    print(f"max_drawdown:   {pf.max_drawdown() * 100:.4f}")
    print(f"total_return:   {pf.total_return() * 100:.4f}")
    print(f"win_rate:       {pf.trades.win_rate() * 100:.1f}")
    print(f"total_trades:   {pf.trades.count()}")
    print(f"profit_factor:  {pf.trades.profit_factor():.4f}")
    print(f"final_value:    {pf.final_value():.0f}")


def export_trades(pf):
    """Export trade log to CSV."""
    trades_file = script_dir / "SBIN_trades.csv"
    pf.trades.records_readable.to_csv(trades_file, index=False)
    log.info(f"Trades exported to {trades_file}")


# --- Main ---
if __name__ == "__main__":
    from strategy import generate_signals

    df, df_bench = load_data()
    entries, exits = generate_signals(df)
    pf = run_backtest(df, entries, exits)
    pf_bench = run_benchmark(df, df_bench)
    score = compute_score(pf)
    print_results(pf, pf_bench, score)
    export_trades(pf)
