"""
Strategy file — the AI agent modifies ONLY this file.
"""

import numpy as np
import pandas as pd
import talib as tl


# --- Hyperparameters ---
EMA_FAST = 10
EMA_SLOW = 30
ADX_PERIOD = 14
ADX_THRESHOLD = 25
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70


def exrem(signal1, signal2):
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
    close = df["close"]
    high = df["high"]
    low = df["low"]

    ema_fast = pd.Series(tl.EMA(close.values, timeperiod=EMA_FAST), index=close.index)
    ema_slow = pd.Series(tl.EMA(close.values, timeperiod=EMA_SLOW), index=close.index)
    adx = pd.Series(tl.ADX(high.values, low.values, close.values, timeperiod=ADX_PERIOD), index=close.index)
    rsi = pd.Series(tl.RSI(close.values, timeperiod=RSI_PERIOD), index=close.index)

    buy_raw = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
    sell_raw = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))

    # Filters: strong trend + not overbought
    buy_raw = buy_raw & (adx > ADX_THRESHOLD) & (rsi < RSI_OVERBOUGHT)

    entries = exrem(buy_raw.fillna(False), sell_raw.fillna(False))
    exits = exrem(sell_raw.fillna(False), buy_raw.fillna(False))

    return entries, exits
