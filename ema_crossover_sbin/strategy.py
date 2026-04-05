"""
Strategy file — the AI agent modifies ONLY this file.

Must export: generate_signals(df) -> (entries: pd.Series[bool], exits: pd.Series[bool])

Available in df: open, high, low, close, volume (lowercase, DatetimeIndex)
Available libraries: talib, numpy, pandas, sklearn (PCA, classifiers, etc.)
"""

import numpy as np
import pandas as pd
import talib as tl


# --- Hyperparameters ---
EMA_FAST = 10
EMA_SLOW = 30


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


def generate_signals(df):
    """
    Generate entry and exit signals.

    Args:
        df: DataFrame with columns [open, high, low, close, volume], DatetimeIndex

    Returns:
        (entries, exits): tuple of boolean pd.Series, same index as df
    """
    close = df["close"]

    # --- Indicators ---
    ema_fast = pd.Series(tl.EMA(close.values, timeperiod=EMA_FAST), index=close.index)
    ema_slow = pd.Series(tl.EMA(close.values, timeperiod=EMA_SLOW), index=close.index)

    # --- Raw signals ---
    buy_raw = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
    sell_raw = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))

    # --- Clean signals ---
    entries = exrem(buy_raw.fillna(False), sell_raw.fillna(False))
    exits = exrem(sell_raw.fillna(False), buy_raw.fillna(False))

    return entries, exits
