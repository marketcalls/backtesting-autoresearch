# autobacktest

Autonomous AI-driven strategy optimization for SBIN EMA crossover.

## Setup

To set up a new experiment run, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `apr5`). The branch `autobacktest/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autobacktest/<tag>` from current master.
3. **Read the in-scope files**:
   - `program.md` — this file. Your instructions.
   - `backtest.py` — fixed harness. Data loading, portfolio simulation, scoring, output. Do not modify.
   - `strategy.py` — the file you modify. Signal generation logic.
4. **Initialize results.tsv**: Create `results.tsv` with just the header row. The baseline will be recorded after the first run.
5. **Confirm and go**: Confirm setup looks good, then kick off experimentation.

## Goal

**Maximize the composite score** (printed as `score:` in the output). The score combines:

- **40% CAGR** — reward absolute returns
- **30% Sharpe Ratio** — reward risk-adjusted returns  
- **30% (100 - |MaxDD%|)** — reward capital preservation

Higher score = better. The baseline EMA 10/30 crossover is your starting point.

## What you CAN modify

Only `strategy.py`. The function signature must remain: `generate_signals(df) -> (entries, exits)`

**Fair game ideas** (not exhaustive — be creative):

- **Indicator tuning**: Change EMA periods, try SMA, DEMA, TEMA, WMA
- **Additional indicators**: RSI, MACD, ADX, Bollinger Bands, ATR, Stochastic, CCI, MOM, OBV
- **Trend filters**: Only trade when ADX > threshold, or when price > 200 SMA
- **Volatility filters**: Skip trades when ATR is too high/low, or BB width is narrow
- **Volume filters**: Require volume confirmation on crossovers
- **Multi-timeframe**: Use weekly EMA as a trend filter on daily signals
- **Stop-loss / trailing stop logic**: Exit early on adverse moves (via signal logic, not VBT SL)
- **Mean reversion filters**: Use RSI to avoid buying into overbought conditions
- **Regime detection**: Use volatility clustering, trend strength to adapt behavior
- **PCA / ML filters**: Build features from indicators, use PCA to reduce dimensionality, train a simple classifier (logistic regression, random forest) on historical trades to filter out likely losers. Use walk-forward or expanding window to avoid lookahead bias.
- **Seasonality**: Day-of-week or month effects
- **Signal confirmation**: Require N consecutive bars of confirmation before entry
- **Position sizing**: Return different allocation sizes based on signal confidence (modify the entries to encode sizing if needed)

## What you CANNOT modify

- `backtest.py` — it is the fixed evaluation harness
- The function signature `generate_signals(df) -> (entries, exits)`
- Cannot install new packages — only use what's in `pyproject.toml` (talib, numpy, pandas, sklearn, scipy, vectorbt)
- Cannot add lookahead bias — no peeking at future data. All indicators and filters must use only past/current data.

## Available libraries for strategy.py

```python
import talib as tl          # All TA-Lib indicators (EMA, RSI, MACD, BBANDS, ATR, ADX, etc.)
import numpy as np          # Numerical operations
import pandas as pd         # DataFrames, rolling windows
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
# Any other sklearn module already installed
```

## Output format

The backtest prints a machine-readable block:

```
---
score:          20.1234
cagr:           10.7500
sharpe:         0.5246
sortino:        0.7748
max_drawdown:   -46.5138
total_return:   181.0131
win_rate:       40.0
total_trades:   60
profit_factor:  1.9395
final_value:    2810131
```

Extract the key metric: `grep "^score:" run.log`

## Logging results

Log every experiment to `results.tsv` (tab-separated). Header and columns:

```
commit	score	cagr	sharpe	max_dd	trades	status	description
```

1. git commit hash (short, 7 chars)
2. composite score (e.g. 20.1234)
3. CAGR % (e.g. 10.75)
4. Sharpe ratio (e.g. 0.52)
5. Max drawdown % as positive number (e.g. 46.51)
6. Total trades (e.g. 60)
7. status: `keep`, `discard`, or `crash`
8. short description of what this experiment tried

Example:

```
commit	score	cagr	sharpe	max_dd	trades	status	description
a1b2c3d	20.12	10.75	0.52	46.51	60	keep	baseline EMA 10/30
b2c3d4e	24.56	12.30	0.68	38.20	45	keep	add ADX>25 trend filter
c3d4e5f	18.90	9.80	0.45	52.10	55	discard	RSI overbought filter too aggressive
d4e5f6g	0.00	0.00	0.00	0.00	0	crash	PCA feature pipeline bug
```

## The experiment loop

LOOP FOREVER:

1. Check git state: current branch/commit
2. Modify `strategy.py` with an experimental idea
3. `git commit` the change
4. Run: `uv run python ema_crossover_sbin/backtest.py > run.log 2>&1`
5. Extract results: `grep "^score:\|^cagr:\|^sharpe:\|^max_drawdown:\|^total_trades:" run.log`
6. If grep is empty, it crashed. Run `tail -n 50 run.log` to diagnose. Fix if trivial, else skip.
7. Log results to `results.tsv` (do NOT commit results.tsv — leave it untracked)
8. If score improved (higher): keep the commit, advance the branch
9. If score is equal or worse: `git reset --hard HEAD~1` to revert
10. Repeat

## Strategy tips

**Start simple, build up:**
- First run: establish baseline (the current EMA 10/30)
- Then try one change at a time so you know what helped
- Combine winners from previous rounds

**Avoid overfitting:**
- More trades is generally better (more statistical significance)
- If a filter drops trades below ~20, it's probably overfitting
- ML models must use expanding window or walk-forward — never train on full data
- Simple filters (ADX, volume) often beat complex ML approaches

**High-impact ideas to try early:**
1. Trend filter (ADX > 20-25) — avoids choppy/sideways markets
2. EMA period optimization (try 5/20, 8/21, 12/26, 20/50)
3. ATR-based volatility filter — skip low-conviction setups
4. RSI guard — don't buy when RSI > 70 (already overbought)
5. 200 SMA trend filter — only buy when price > 200 SMA

**When stuck:**
- Re-read `strategy.py` and `results.tsv` for patterns
- Try combining 2-3 filters that individually helped
- Try the opposite of what failed (e.g., if tightening a filter hurt, try loosening it)
- Try entirely different indicator families (momentum vs trend vs volatility)

## NEVER STOP

Once the loop begins, do NOT pause to ask the human. They may be away. Run autonomously until manually stopped. If you run out of ideas, think harder — re-read results, try combinations, try radical changes. The loop runs until interrupted.
