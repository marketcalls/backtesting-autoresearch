# Backtesting

VectorBT-based backtesting framework for Indian equity markets with realistic transaction costs (STT + statutory charges + brokerage).

## Setup

```bash
uv venv
uv sync
```

## Usage

```bash
uv run python ema_crossover_sbin/backtest.py
```

## Project Structure

```
backtesting/
├── ema_crossover_sbin/
│   └── backtest.py          # EMA 10/30 crossover strategy for SBIN
├── .env                     # API keys (not committed)
├── pyproject.toml           # Dependencies
└── README.md
```

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
- [Plotly](https://plotly.com/python/) - Charting

## License

MIT License - see [LICENSE](LICENSE) for details.
