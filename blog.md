# I Let an AI Agent Optimize My Trading Strategy Overnight — Here's What Happened

## How 26 autonomous experiments turned a basic EMA crossover into a strategy with a Sharpe ratio above 1.0

---

Here's a quick experiment you can try right now.

Open any charting platform. Pull up SBIN (State Bank of India) on a daily chart. Slap on a 10-period and 30-period EMA. Buy when the fast crosses above the slow, sell when it crosses below. The most basic trend-following strategy in every trading textbook.

Run that for 15 years with Rs 10 lakh. You'll get roughly 10.75% CAGR. Not bad — until you see the **-46.51% max drawdown**. That's your account going from Rs 10 lakh to Rs 5.35 lakh at the worst point. Nearly half your capital, gone. Most people would have stopped trading long before recovering from that.

Now here's the interesting part. I gave an AI agent this exact strategy and a single instruction: *make it better*. No hand-holding, no hints, no guardrails beyond "don't touch the evaluation harness." Just a loop — modify, test, keep or revert, repeat.

26 experiments later, the same EMA crossover backbone now delivers **14.39% CAGR** with a **-15.41% max drawdown** and a **Sharpe ratio above 1.0**. Same stock. Same timeframe. Same entry signal at its core. The drawdown shrank by three times.

What did the AI figure out? And what did it try that failed spectacularly?

---

The idea started when I came across Andrej Karpathy's [autoresearch](https://github.com/karpathy/autoresearch).

---

## What is Autoresearch?

[Autoresearch](https://github.com/karpathy/autoresearch) is a project by Andrej Karpathy — former Tesla AI Director and OpenAI founding member — that lets an AI agent autonomously run research experiments on LLM (Large Language Model) pretraining. You go to sleep, and while you're dreaming about candlestick patterns, the AI is running experiments, evaluating results, and iterating.

The core idea is deceptively simple. The entire system is built on three principles:

**1. Separation of concerns**: Split the project into what's fixed (the evaluation) and what's mutable (the experiment). In Karpathy's version, the fixed part is `prepare.py` — data loading, tokenizer training, the evaluation metric. The mutable part is `train.py` — model architecture, optimizer, hyperparameters. The AI only touches the mutable file.

**2. Objective scoring**: Every experiment produces a single number. In autoresearch, that number is `val_bpb` (validation bits per byte) — lower is better. There's no subjective judgment. The AI doesn't need to "feel" whether a change is good. It just compares numbers.

**3. Git as a research notebook**: Each experiment is a git commit. If the score improves, the commit stays. If it doesn't, `git reset --hard HEAD~1` wipes it clean. The branch history becomes a curated record of every improvement, and the TSV log captures every attempt — including the failures.

The result: Karpathy reports running ~12 experiments per hour, ~100 overnight. The AI tries architectural changes, optimizer tweaks, hyperparameter tuning, and ablations — all without human intervention.

I read that and thought: *This is exactly what strategy optimization needs.*

---

## From LLM Training to Trading: The Adaptation

Trading strategy optimization has the same structure as LLM research:

- There's a **fixed evaluation** — the backtest harness with historical data and realistic fees
- There's a **mutable experiment** — the signal generation logic
- There's a **single metric** to optimize — except in trading, we care about multiple things (returns, risk, drawdown), so we need a composite score
- Each experiment is **fast** — a 15-year daily backtest takes ~30 seconds, not 5 minutes like LLM training

Here's how I adapted the autoresearch pattern for trading:

## The Setup: Three Files, One Rule

| File | Role | Who touches it | Why it's locked/unlocked |
|------|------|----------------|--------------------------|
| `backtest.py` | Fixed harness — data loading, portfolio simulation, scoring | **Nobody** | Prevents the AI from gaming the evaluation (e.g., changing fee calculations, cherry-picking date ranges, or modifying the scoring formula to inflate results) |
| `strategy.py` | Signal generation logic — indicators, filters, entry/exit rules | **AI agent only** | This is the experiment. Everything inside is fair game: indicators, parameters, filters, ML models, exit logic |
| `program.md` | Instructions for the AI — what to optimize, how to log results, the experiment loop | **Human only** | This is how the human "programs" the AI without writing code. Change the instructions to steer the research direction |

The separation matters. If the AI could modify `backtest.py`, it might learn to reduce fees to zero, shorten the test period to a favorable window, or change the score formula. That's not optimization — that's cheating. By locking the harness, every improvement has to come from genuinely better trading logic.

### What the AI CAN do in strategy.py

The function signature is fixed — `generate_signals(df)` takes in a DataFrame with OHLCV columns and returns `(entries, exits)` as boolean Series. Within that contract, everything is fair game:

- Change indicator types and periods (EMA, SMA, DEMA, TEMA)
- Add filters (ADX, RSI, volume, Bollinger Bands, ATR)
- Build ML models (Random Forest, Logistic Regression, PCA) with walk-forward training
- Implement trailing stops, mean-reversion exits, momentum confirmation
- Combine multiple indicators in any way it can imagine

### What the AI CANNOT do

- Modify `backtest.py` — no changing fees, date ranges, initial capital, or scoring
- Install new packages — only use what's already in `pyproject.toml`
- Introduce lookahead bias — all indicators and filters must use only past/current data
- Change the function signature — must return `(entries, exits)` boolean Series

### The Instructions (program.md)

The `program.md` file is essentially a prompt that tells the AI how to behave. It contains:

- **The goal**: Maximize the composite score
- **The experiment loop**: Modify, commit, run, evaluate, keep/revert, log, repeat
- **Strategy tips**: Start simple, one change at a time, combine winners
- **Anti-overfitting rules**: Keep trades above ~20, use walk-forward for ML, prefer simple filters
- **The critical instruction**: *NEVER STOP*. The human might be asleep. Run until manually interrupted.

This last part is key. The AI doesn't pause after each experiment to ask "should I continue?" It just keeps going, autonomously, until you come back and Ctrl+C it.

### The Scoring Formula

For evaluation, I designed a composite score that balances three things traders care about:

```
score = (CAGR% x 0.4) + (Sharpe x 10 x 0.3) + ((100 - |MaxDD%|) x 0.3)
```

- **40% weight on CAGR** — because returns matter
- **30% weight on Sharpe ratio** — because risk-adjusted returns matter more
- **30% weight on drawdown protection** — because surviving to trade another day matters most

Why not just maximize CAGR? Because a strategy that returns 25% but draws down 60% will blow up your account in practice. The composite score forces the AI to find strategies that are *good enough* on returns while being *excellent* on risk management. A strategy with 14% CAGR and 15% drawdown scores higher than one with 20% CAGR and 50% drawdown — and that's exactly the tradeoff a real trader would make.

The data: 15 years of daily SBIN (State Bank of India) from [yfinance](https://github.com/ranaroussi/yfinance), with realistic Indian market transaction costs — STT, statutory charges, and Rs 20/order brokerage.

---

## The Baseline: A Textbook EMA Crossover

Every journey needs a starting point. Mine was the most vanilla strategy you can write — an EMA 10/30 crossover:

- **Buy** when the 10-day EMA crosses above the 30-day EMA
- **Sell** when it crosses below

15 years of SBIN, Rs 10 lakh starting capital, realistic fees. Here's what you get:

| Metric | Value |
|--------|-------|
| CAGR | 10.75% |
| Sharpe Ratio | 0.52 |
| Max Drawdown | **-46.51%** |
| Win Rate | 40% |
| Total Trades | 60 |
| Score | 21.92 |

Not terrible. Not great. A 46% drawdown means at some point, your Rs 10 lakh account would have been sitting at Rs 5.35 lakh. That's the kind of drawdown that makes you close the app and question your life choices.

Can an AI do better?

---

## The Loop: 26 Experiments, Zero Human Intervention

I pointed [Claude Code](https://claude.ai/claude-code) at the project, loaded the [vectorbt-expert skill](https://skills.sh/marketcalls/vectorbt-backtesting-skills/vectorbt-expert) for backtesting domain knowledge, and told it to start the autonomous loop.

The workflow for each experiment:

1. Modify `strategy.py` with an idea
2. Git commit
3. Run the backtest (`uv run python ema_crossover_sbin/backtest.py`)
4. Extract the score via grep
5. If score improved — keep the commit
6. If not — `git reset --hard HEAD~1`
7. Log everything to `results.tsv`
8. Repeat

Each experiment takes about 30 seconds. The AI ran 26 experiments in a single session. Here's the journey, compressed.

---

## Phase 1: Trend Filters (Experiments 2-5)

The AI's first instinct was smart — stop trading in sideways markets.

**ADX > 25 filter**: Only enter when the Average Directional Index signals a strong trend. Score jumped from 21.92 to 24.81. Max drawdown dropped from -46% to -22%. But CAGR collapsed to 2.2% with only 10 trades. Too aggressive.

**200 SMA filter on top**: Only buy when price is above the 200-day SMA. Negative CAGR, 6 trades. Dead end.

The AI learned: *ADX works, but 25 is too strict. The filter needs to be loose enough to let good trades through.*

---

## Phase 2: The ATR Trailing Stop Breakthrough (Experiments 7-12)

This was the turning point.

Instead of just filtering entries, the AI attacked the exit side. It added an **ATR-based trailing stop** — tracking the peak price since entry and exiting when price drops more than N times the Average True Range.

With a 2x ATR trailing stop alone (no entry filters), score jumped to 26.63. CAGR was 11.06% with 60 trades. But max drawdown was still -32%.

Then the AI combined the trailing stop with ADX filtering and systematically tuned:

| ATR Multiplier | Score | CAGR | MaxDD |
|---------------|-------|------|-------|
| 2.0x | 30.66 | 13.52% | -23.72% |
| 1.5x | 32.70 | 13.67% | -18.20% |
| **1.75x** | **33.95** | **13.80%** | **-15.41%** |
| 1.0x | 29.66 | 7.61% | -18.14% |

The 1.75x multiplier was the Goldilocks zone — tight enough to cut losses, loose enough to let winners run.

---

## Phase 3: Stacking Filters That Actually Work (Experiments 14-23)

With the core engine solid (EMA crossover + ATR trailing stop + ADX > 15), the AI started testing additional filters:

**Volume confirmation** (kept): Requiring volume above the 20-day moving average improved the score to 33.24. The logic is sound — a crossover on low volume is less convincing than one on high volume.

**RSI overbought guard** (kept, but tuned): Initially RSI < 70 was tested. It helped. But then the AI tried RSI < 80 and got a *better* result — score 34.25. The insight: RSI 70 is too conservative for a trend-following strategy. You *want* to enter strong trends, and those often have RSI between 70-80.

**Bollinger Band width** (discarded): Adding a BB width expansion filter dropped the score. Too many filters stacking.

**MACD histogram exit** (discarded): Achieved the best-ever max drawdown (-13.51%) but at the cost of CAGR. A tradeoff the scoring formula correctly rejected.

---

## Phase 4: The ML Experiment That Failed (Experiment 18)

This was the experiment I was most curious about.

The AI built a **Random Forest classifier** with walk-forward training. For each potential trade, it:

1. Computed features: ADX, RSI, volume ratio, ATR%, EMA spread, 5-day and 20-day returns
2. Trained on all previous trade outcomes (expanding window — no lookahead bias)
3. Predicted whether the current trade would be profitable
4. Filtered out predicted losers

Score: **27.43**. Worse than even simple ADX filtering alone.

Why? With only ~60 total crossovers over 15 years, there simply aren't enough training samples. The Random Forest was either overfitting to noise or being too conservative. Simple rule-based filters — developed from decades of market microstructure knowledge — beat the ML approach handily.

This is an important result. **ML is not magic. On small sample sizes, domain expertise encoded as simple rules wins.**

---

## Phase 5: Diminishing Returns (Experiments 20-26)

The AI kept trying:
- EMA 5/20 (too fast — MaxDD exploded to -35%)
- 5-day momentum confirmation (marginal loss)
- Re-entry after ATR stop (85 trades, whipsaw disaster)
- ADX > 18 fine-tuning (marginal, not worth the complexity)

Each attempt either matched or slightly worsened the score. The strategy had converged.

---

## The Final Strategy

After 26 experiments, here's what the AI settled on:

```
Entry Conditions (ALL must be true):
  1. EMA(10) crosses above EMA(30)
  2. ADX(14) > 15           — trend is present
  3. RSI(14) < 80           — not extremely overbought
  4. Volume > 20-day avg    — conviction confirmed

Exit Conditions (ANY triggers exit):
  1. EMA(10) crosses below EMA(30)
  2. Price drops 1.75x ATR(14) from peak since entry
```

---

## Before and After

| Metric | Baseline | Optimized | Improvement |
|--------|----------|-----------|-------------|
| **Score** | 21.92 | **34.25** | +56% |
| **CAGR** | 10.75% | **14.39%** | +34% |
| **Sharpe Ratio** | 0.52 | **1.04** | +100% |
| **Max Drawdown** | -46.51% | **-15.41%** | 3x better |
| **Trades** | 60 | 28 | Fewer, higher quality |

The CAGR now nearly matches buy-and-hold NIFTY 50 (14.46%), but with **one-third the drawdown** and a Sharpe ratio above 1.0.

In practical terms: on a Rs 10 lakh account, the worst temporary loss went from Rs 4.65 lakh to Rs 1.54 lakh. That's the difference between panic-selling and sleeping peacefully.

---

## What I Learned

### 1. The autoresearch pattern works for trading

The three-file architecture (fixed harness + mutable strategy + instructions) is remarkably effective. The AI stays focused, the evaluation is objective, and the git history becomes a research notebook.

### 2. Simple beats complex

ADX + RSI + Volume + ATR trailing stop. Four indicators, clean logic. The Random Forest ML filter, Bollinger Band width analysis, MACD histogram exit, and re-entry logic all failed to beat these simple rules. In a domain with small sample sizes (28 trades over 15 years), parsimony wins.

### 3. Exit strategy matters more than entry

The single biggest improvement came from the ATR trailing stop — not from any entry filter. Most traders obsess over when to buy. The AI quickly figured out that *how you exit* has a much larger impact on drawdown and risk-adjusted returns.

### 4. Filter tuning is non-obvious

RSI < 70 is the textbook overbought level. But RSI < 80 performed better for a trend-following strategy. ADX > 25 is the standard "strong trend" threshold, but ADX > 15 was optimal here. The "right" parameter values depend on the strategy context, not on textbook defaults.

### 5. Diminishing returns are real

The first 10 experiments took the score from 21.92 to 33.24. The next 16 experiments improved it by just 1.01 more points. Know when to stop optimizing.

---

## Try It Yourself

The full project is open source:

**GitHub**: [marketcalls/backtesting-autoresearch](https://github.com/marketcalls/backtesting-autoresearch)

```bash
git clone https://github.com/marketcalls/backtesting-autoresearch.git
cd backtesting-autoresearch
uv venv && uv sync
uv run python ema_crossover_sbin/backtest.py
```

To run the autonomous loop, point Claude Code at `program.md` and let it go.

---

## Credits and Tools

- **[autoresearch](https://github.com/karpathy/autoresearch)** by Andrej Karpathy — the original inspiration for the autonomous research loop pattern
- **[Claude Code](https://claude.ai/claude-code)** by Anthropic — the AI agent that ran all 26 experiments
- **[vectorbt-expert skill](https://skills.sh/marketcalls/vectorbt-backtesting-skills/vectorbt-expert)** — backtesting domain knowledge skill for Claude Code
- **[VectorBT](https://github.com/polakowo/vectorbt)** by Oleg Polakow — vectorized backtesting engine
- **[TA-Lib](https://github.com/TA-Lib/ta-lib-python)** — technical indicator library (EMA, RSI, ADX, ATR)
- **[yfinance](https://github.com/ranaroussi/yfinance)** — Yahoo Finance market data
- **[OpenAlgo](https://openalgo.in)** — Indian market trading platform and data API
- **[uv](https://github.com/astral-sh/uv)** by Astral — fast Python package manager

---

*Disclaimer: This is a research project, not financial advice. Past performance does not guarantee future results. Always validate strategies with out-of-sample data and paper trading before risking real capital.*

---

*If you found this interesting, the code is on [GitHub](https://github.com/marketcalls/backtesting-autoresearch). Star it, fork it, run your own experiments. The autonomous loop pattern works for any strategy — not just EMA crossovers.*
