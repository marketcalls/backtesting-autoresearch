# Backtesting

VectorBT-based backtesting framework for Indian equity markets with realistic transaction costs (STT + statutory charges + brokerage). Includes an autonomous AI-driven strategy optimization loop.

## Setup

```bash
uv venv
uv sync
```

## Usage

```bash
# Run a single backtest
uv run python ema_crossover_sbin/backtest.py

# Start autonomous optimization (read program.md first)
# The AI agent modifies strategy.py and loops automatically
```

## Project Structure

```
backtesting/
├── ema_crossover_sbin/
│   ├── backtest.py          # Fixed harness: data, portfolio, scoring (DO NOT MODIFY)
│   ├── strategy.py          # Signal generation (AI agent modifies THIS)
│   ├── program.md           # Instructions for autonomous experimentation
│   └── results.tsv          # Experiment log (untracked)
├── .env                     # API keys (not committed)
├── pyproject.toml           # Dependencies
└── README.md
```

## Autonomous Research Workflow

Inspired by [autoresearch](https://github.com/karpathy/autoresearch). The AI agent:

1. Modifies `strategy.py` with an experimental idea
2. Runs the backtest (~30s per experiment)
3. Evaluates a composite score (higher = better)
4. Keeps improvements, reverts failures
5. Logs results to `results.tsv`
6. Repeats indefinitely

### Composite Score Formula

```
score = (CAGR% x 0.4) + (Sharpe x 10 x 0.3) + ((100 - |MaxDD%|) x 0.3)
```

| Weight | Component | What it rewards |
|--------|-----------|----------------|
| 40% | CAGR % | Absolute returns (higher CAGR = more growth) |
| 30% | Sharpe x 10 | Risk-adjusted returns (higher Sharpe = better return per unit of risk) |
| 30% | 100 - \|MaxDD%\| | Capital preservation (lower drawdown = less pain) |

**Example** — Baseline (CAGR=10.75, Sharpe=0.52, MaxDD=46.51):
```
score = (10.75 x 0.4) + (0.52 x 10 x 0.3) + ((100 - 46.51) x 0.3)
      = 4.30 + 1.56 + 16.05
      = 21.92
```

**Example** — Final best (CAGR=14.39, Sharpe=1.04, MaxDD=15.41):
```
score = (14.39 x 0.4) + (1.04 x 10 x 0.3) + ((100 - 15.41) x 0.3)
      = 5.76 + 3.12 + 25.38
      = 34.25
```

The formula balances growth, risk efficiency, and downside protection. A strategy that returns 20% CAGR but draws down 60% scores lower than one returning 14% with only 15% drawdown.

## Final Optimized Strategy

**Symbol**: SBIN.NS (State Bank of India) | **Timeframe**: Daily | **Period**: 15 years

### Components

| Component | Type | Details |
|-----------|------|---------|
| EMA 10/30 Crossover | Entry Signal | Buy when EMA(10) crosses above EMA(30) |
| ADX > 15 | Trend Filter | Only enter when trend strength is sufficient |
| RSI < 80 | Overbought Guard | Block entries in extreme overbought conditions |
| Volume > 20-day MA | Volume Filter | Require above-average volume confirmation |
| 1.75x ATR Trailing Stop | Exit | Exit when price drops 1.75x ATR from peak since entry |
| EMA Bearish Cross | Exit | Exit when EMA(10) crosses below EMA(30) |

### Performance: Baseline vs Optimized

| Metric | Baseline | Optimized | Change |
|--------|----------|-----------|--------|
| **Score** | 21.92 | **34.25** | +56.3% |
| **CAGR** | 10.75% | **14.39%** | +3.64pp |
| **Sharpe Ratio** | 0.52 | **1.04** | +100% |
| **Max Drawdown** | -46.51% | **-15.41%** | -31.1pp |
| **Win Rate** | 40.0% | improved | - |
| **Total Trades** | 60 | 28 | fewer, higher quality |

## Experiment Log

26 experiments were conducted across 7 categories. Each row shows the experiment result and whether it was kept or discarded.

### Kept Experiments (Progressive Improvements)

| # | Score | CAGR | Sharpe | MaxDD | Trades | Category | Description |
|---|-------|------|--------|-------|--------|----------|-------------|
| 1 | 21.92 | 10.75% | 0.52 | -46.51% | 60 | Baseline | EMA 10/30 crossover |
| 2 | 24.81 | 2.21% | 0.24 | -22.65% | 10 | Trend Filter | ADX > 25 |
| 5 | 26.42 | 2.74% | 0.30 | -18.55% | 8 | Momentum Filter | ADX > 25 + RSI < 70 |
| 7 | 26.63 | 11.06% | 0.64 | -32.36% | 60 | Exit Strategy | ATR 2.0x trailing stop |
| 9 | 30.66 | 13.52% | 0.79 | -23.72% | 46 | Trend Filter | ATR trailing + ADX > 15 |
| 11 | 32.70 | 13.67% | 0.90 | -18.20% | 43 | Exit Tuning | ATR 1.5x tighter stop |
| 14 | 33.24 | 12.32% | 0.98 | -15.41% | 26 | Volume Filter | Volume > 20-day MA |
| 19 | 33.95 | 13.80% | 1.02 | -15.41% | 26 | Exit Tuning | ATR 1.75x sweet spot |
| 23 | **34.25** | **14.39%** | **1.04** | **-15.41%** | 28 | Momentum Filter | RSI < 80 (final best) |

### All Experiments by Category

| Category | Experiments | Best Outcome | Key Insight |
|----------|-------------|-------------|-------------|
| **Trend Filters** (ADX) | ADX>25, ADX>20, ADX>15, ADX>18, ADX>10 | ADX>15 optimal | ADX>25 too strict (kills CAGR), ADX>10 too loose (noise) |
| **Momentum Filters** (RSI) | RSI<70, RSI<80, RSI<30 exit, no RSI | RSI<80 optimal | RSI<70 blocks valid strong-trend entries, RSI<80 filters only extremes |
| **Exit Strategies** (ATR) | ATR 2.0x, 1.5x, 1.75x, 1.0x | ATR 1.75x optimal | 1.0x cuts winners too early, 2.0x lets losers run too long |
| **Volume Filters** | Volume > 20-day MA | Kept | Adds conviction check, reduces bad entries |
| **EMA Period Tuning** | 10/30, 8/21, 12/26, 5/20 | 10/30 original best | Faster EMAs increase noise, slower ones miss moves |
| **ML/Complex** | Random Forest walk-forward, BB width, MACD exit, re-entry logic | All discarded | Simple rule-based filters beat ML on small trade samples |
| **Multi-Filter Combos** | ADX+SMA200, ADX+RSI+Volume+BB, momentum confirm | Mostly discarded | Stacking too many filters reduces trades below useful levels |

### Discarded Experiments

| # | Score | Description | Reason |
|---|-------|-------------|--------|
| 3 | 21.09 | EMA 8/21 + ADX>20 | Worse drawdown and CAGR |
| 4 | 22.35 | ADX>25 + 200 SMA | Too few trades (6), negative CAGR |
| 6 | 26.42 | RSI<30 early exit | No effect (never triggered) |
| 12 | 29.66 | ATR 1.0x | Too tight, cuts winners |
| 13 | 32.44 | EMA 12/26 | Slightly worse MaxDD |
| 15 | 31.71 | BB width expanding | Too many filters stacked |
| 16 | 33.12 | MACD histogram exit | Best DD (-13.5%) but lower CAGR |
| 17 | 31.33 | ADX>10 | Too loose, lets noise through |
| 18 | 27.43 | Random Forest ML filter | Walk-forward ML worse than simple rules |
| 20 | 33.91 | Remove RSI entirely | Sharpe drops below 1.0 |
| 21 | 27.54 | EMA 5/20 | Too fast, MaxDD blows up to -35% |
| 22 | 33.46 | 5-day momentum filter | Marginal loss, blocks valid trades |
| 24 | 33.91 | No RSI at all | Confirms RSI<80 adds value |
| 25 | 33.96 | ADX>18 | Too strict, drops CAGR |
| 26 | 25.16 | Re-entry after ATR stop | Whipsaw disaster (85 trades) |

## Configuration

Copy `.env` and set your API keys if using OpenAlgo:

```
OPENALGO_API_KEY=your_key_here
OPENALGO_HOST=http://127.0.0.1:5000
```

## Tech Stack

- [VectorBT](https://github.com/polakowo/vectorbt) - Vectorized backtesting
- [TA-Lib](https://github.com/TA-Lib/ta-lib-python) - Technical indicators
- [yfinance](https://github.com/ranaroussi/yfinance) - Market data
- [scikit-learn](https://scikit-learn.org/) - ML filters (PCA, classifiers)
- [Plotly](https://plotly.com/python/) - Charting

## License

MIT License - see [LICENSE](LICENSE) for details.
