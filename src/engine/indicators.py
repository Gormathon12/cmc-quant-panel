"""
Technical indicators — pure functions over price/volume series.

All list-returning indicators are aligned with the input series (None for the
warmup region) so signal generators can index by candle position without offset
bugs. No look-ahead: each value uses only data up to and including its own index.
"""

import math


def ema(data: list, period: int) -> list:
    """Exponential Moving Average, seeded with an SMA. None during warmup."""
    result = [None] * len(data)
    if len(data) < period:
        return result
    k = 2 / (period + 1)
    sma = sum(data[:period]) / period
    result[period - 1] = sma
    for i in range(period, len(data)):
        result[i] = data[i] * k + result[i - 1] * (1 - k)
    return result


def rsi(closes: list, period: int = 14) -> list:
    """Wilder's RSI aligned with closes (None for the first `period` values)."""
    result = [None] * len(closes)
    if len(closes) <= period:
        return result
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for i in range(period, len(closes)):
        idx = i - 1
        if i > period:
            avg_g = (avg_g * (period - 1) + gains[idx]) / period
            avg_l = (avg_l * (period - 1) + losses[idx]) / period
        if avg_l > 0:
            rsi_val = 100 - (100 / (1 + avg_g / avg_l))
        else:
            rsi_val = 100 if avg_g > 0 else 50
        result[i] = round(rsi_val, 2)
    return result


def donchian_high(highs: list, period: int = 20) -> list:
    result = [None] * len(highs)
    for i in range(period - 1, len(highs)):
        result[i] = max(highs[i - period + 1: i + 1])
    return result


def donchian_low(lows: list, period: int = 20) -> list:
    result = [None] * len(lows)
    for i in range(period - 1, len(lows)):
        result[i] = min(lows[i - period + 1: i + 1])
    return result


def bollinger(closes: list, period: int = 20, mult: float = 2.0):
    """Returns (upper, middle, lower) lists aligned with closes."""
    upper = [None] * len(closes)
    middle = [None] * len(closes)
    lower = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1: i + 1]
        sma = sum(window) / period
        std = math.sqrt(sum((x - sma) ** 2 for x in window) / period)
        upper[i] = sma + mult * std
        middle[i] = sma
        lower[i] = sma - mult * std
    return upper, middle, lower


def volume_ma(volumes: list, period: int = 20) -> list:
    result = [None] * len(volumes)
    for i in range(period - 1, len(volumes)):
        result[i] = sum(volumes[i - period + 1: i + 1]) / period
    return result


def macd(closes: list, fast: int = 12, slow: int = 26, signal: int = 9):
    """Returns (macd_line, signal_line, histogram) aligned with closes."""
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = [None] * len(closes)
    for i in range(len(closes)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]

    first_valid = next((i for i, v in enumerate(macd_line) if v is not None), None)
    signal_line = [None] * len(closes)
    if first_valid is not None:
        valid_segment = macd_line[first_valid:]
        signal_raw = ema(valid_segment, signal)
        for j, val in enumerate(signal_raw):
            signal_line[first_valid + j] = val

    histogram = [None] * len(closes)
    for i in range(len(closes)):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram[i] = macd_line[i] - signal_line[i]
    return macd_line, signal_line, histogram


def atr(highs: list, lows: list, closes: list, period: int = 14) -> list:
    """Wilder's Average True Range aligned with closes."""
    result = [None] * len(closes)
    if len(closes) <= period:
        return result
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i],
                       abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    seed = sum(trs[1:period + 1]) / period
    result[period] = seed
    for i in range(period + 1, len(closes)):
        result[i] = (result[i - 1] * (period - 1) + trs[i]) / period
    return result


def snapshot(candles: list) -> dict:
    """
    Current-state indicator snapshot from a candle list: RSI-14, ATR%, EMA-50/200,
    and a coarse trend label. Used by the Market Scout for regime classification.
    """
    if not candles:
        return {"rsi_14": 50.0, "atr_pct": 2.0, "ema_50": 0, "ema_200": 0,
                "trend": "ranging", "price": 0}

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    price = closes[-1]

    rsi_series = rsi(closes, 14)
    rsi_last = next((v for v in reversed(rsi_series) if v is not None), 50.0)

    atr_series = atr(highs, lows, closes, 14)
    atr_last = next((v for v in reversed(atr_series) if v is not None), 0.0)
    atr_pct = (atr_last / price * 100) if price > 0 else 2.0

    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    ema50_last = next((v for v in reversed(ema50) if v is not None), price)
    ema200_last = next((v for v in reversed(ema200) if v is not None), price)

    if price > ema50_last > ema200_last:
        trend = "strong_uptrend"
    elif price > ema200_last:
        trend = "uptrend"
    elif price < ema50_last < ema200_last:
        trend = "strong_downtrend"
    elif price < ema200_last:
        trend = "downtrend"
    else:
        trend = "ranging"

    return {
        "rsi_14": round(rsi_last, 1),
        "atr_pct": round(atr_pct, 2),
        "ema_50": round(ema50_last, 4),
        "ema_200": round(ema200_last, 4),
        "trend": trend,
        "price": round(price, 4),
    }
