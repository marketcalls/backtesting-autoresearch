"""
Strategy file — the AI agent modifies ONLY this file.
"""

import numpy as np
import pandas as pd
import talib as tl


# --- Hyperparameters ---
EMA_FAST = 10
EMA_SLOW = 30
ATR_PERIOD = 14
ATR_MULTIPLIER = 2.0
ADX_PERIOD = 14
ADX_THRESHOLD = 15


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
    atr = pd.Series(tl.ATR(high.values, low.values, close.values, timeperiod=ATR_PERIOD), index=close.index)
    adx = pd.Series(tl.ADX(high.values, low.values, close.values, timeperiod=ADX_PERIOD), index=close.index)

    buy_raw = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
    sell_ema = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))

    # ADX entry filter
    buy_raw = buy_raw & (adx > ADX_THRESHOLD)

    # ATR trailing stop exit
    in_trade = False
    peak_price = 0.0
    atr_stop = pd.Series(False, index=close.index)

    for i in range(len(close)):
        if buy_raw.iloc[i] and not in_trade:
            in_trade = True
            peak_price = close.iloc[i]
        if in_trade:
            peak_price = max(peak_price, close.iloc[i])
            trail_stop = peak_price - ATR_MULTIPLIER * atr.iloc[i] if not np.isnan(atr.iloc[i]) else 0
            if close.iloc[i] < trail_stop:
                atr_stop.iloc[i] = True
                in_trade = False
        if sell_ema.iloc[i]:
            in_trade = False
            peak_price = 0.0

    sell_raw = sell_ema | atr_stop

    entries = exrem(buy_raw.fillna(False), sell_raw.fillna(False))
    exits = exrem(sell_raw.fillna(False), buy_raw.fillna(False))

    return entries, exits
