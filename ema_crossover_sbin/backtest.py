import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import talib as tl
import vectorbt as vbt
import yfinance as yf

# --- Config ---
script_dir = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

SYMBOL = "SBIN.NS"
BENCHMARK_TICKER = "^NSEI"
INIT_CASH = 1_000_000
FEES = 0.00111              # Indian delivery equity (STT + statutory)
FIXED_FEES = 20             # Rs 20 per order
ALLOCATION = 0.95
EMA_FAST = 10
EMA_SLOW = 30

# --- Fetch Data (15 years) ---
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=365 * 15)).strftime("%Y-%m-%d")

log.info(f"Fetching {SYMBOL} from {start_date} to {end_date}")
df = yf.download(SYMBOL, start=start_date, end=end_date,
                 interval="1d", auto_adjust=True, multi_level_index=False)
df.columns = df.columns.str.lower()
df = df.sort_index()
if df.index.tz is not None:
    df.index = df.index.tz_convert(None)
close = df["close"]
log.info(f"Loaded {len(df)} bars from {df.index[0].date()} to {df.index[-1].date()}")

# --- Indicators (TA-Lib) ---
ema_fast = pd.Series(tl.EMA(close.values, timeperiod=EMA_FAST), index=close.index)
ema_slow = pd.Series(tl.EMA(close.values, timeperiod=EMA_SLOW), index=close.index)

# --- Signals ---
buy_raw = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
sell_raw = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))

# Clean signals with exrem
def exrem(signal1, signal2):
    """Remove consecutive duplicates - keep only first signal in each sequence."""
    result = signal1.copy()
    active = False
    for i in range(len(signal1)):
        if active:
            result.iloc[i] = False
        if signal1.iloc[i] and not active:
            active = True
        if signal2.iloc[i]:
            active = False
    return result

entries = exrem(buy_raw.fillna(False), sell_raw.fillna(False))
exits = exrem(sell_raw.fillna(False), buy_raw.fillna(False))

log.info(f"Total entry signals: {entries.sum()}, exit signals: {exits.sum()}")

# --- Backtest ---
pf = vbt.Portfolio.from_signals(
    close, entries, exits,
    init_cash=INIT_CASH, size=ALLOCATION, size_type="percent",
    fees=FEES, fixed_fees=FIXED_FEES, direction="longonly",
    min_size=1, size_granularity=1, freq="1D",
)

# --- Benchmark (NIFTY 50) ---
log.info(f"Fetching benchmark {BENCHMARK_TICKER}")
df_bench = yf.download(BENCHMARK_TICKER, start=start_date, end=end_date,
                       interval="1d", auto_adjust=True, multi_level_index=False)
df_bench.columns = df_bench.columns.str.lower()
df_bench = df_bench.sort_index()
if df_bench.index.tz is not None:
    df_bench.index = df_bench.index.tz_convert(None)
bench_close = df_bench["close"].reindex(close.index).ffill().bfill()
pf_bench = vbt.Portfolio.from_holding(bench_close, init_cash=INIT_CASH, fees=FEES, freq="1D")

# --- Results ---
print("\n" + "=" * 60)
print(f"EMA CROSSOVER ({EMA_FAST}/{EMA_SLOW}) - {SYMBOL} - Daily")
print(f"Period: {df.index[0].date()} to {df.index[-1].date()}")
print("=" * 60)

print("\n--- Full Stats ---")
print(pf.stats())

# --- Strategy vs Benchmark ---
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

# --- Plain Language Explanation ---
print("\n--- What This Means ---")
strat_ret = pf.total_return() * 100
bench_ret = pf_bench.total_return() * 100
max_dd = pf.max_drawdown() * 100
win_rate = pf.trades.win_rate() * 100

print(f"* Starting with Rs {INIT_CASH:,}, the strategy grew to Rs {pf.final_value():,.0f}")
print(f"* Total return: {strat_ret:.2f}% vs NIFTY {bench_ret:.2f}%")
if strat_ret > bench_ret:
    print(f"  -> Strategy OUTPERFORMED NIFTY by {strat_ret - bench_ret:.2f}%")
else:
    print(f"  -> Strategy UNDERPERFORMED NIFTY by {bench_ret - strat_ret:.2f}%")
print(f"* Max drawdown: {max_dd:.2f}%")
print(f"  -> Worst temporary loss from peak = Rs {abs(pf.max_drawdown()) * INIT_CASH:,.0f}")
print(f"* Win rate: {win_rate:.1f}% across {pf.trades.count()} trades")
print(f"* Profit factor: {pf.trades.profit_factor():.2f} (>1 means profits exceed losses)")

# --- Export Trades ---
trades_file = script_dir / "SBIN_trades.csv"
pf.trades.records_readable.to_csv(trades_file, index=False)
log.info(f"Trades exported to {trades_file}")
