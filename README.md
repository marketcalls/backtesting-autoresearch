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
│   └── program.md           # Instructions for autonomous experimentation
├── .env                     # API keys (not committed)
├── pyproject.toml           # Dependencies
└── README.md
```

## Autonomous Research Workflow

Inspired by [autoresearch](https://github.com/karpathy/autoresearch). The AI agent:

1. Modifies `strategy.py` with an experimental idea
2. Runs the backtest (~30s per experiment)
3. Evaluates a composite score (CAGR 40% + Sharpe 30% + DrawdownProtection 30%)
4. Keeps improvements, reverts failures
5. Logs results to `results.tsv`
6. Repeats indefinitely

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
