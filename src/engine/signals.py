"""
Signal generators — one per strategy family.

Each generator takes price/volume series and returns a list aligned with the
candles where +1 = long entry, -1 = short entry, 0 = no signal. Signals are
consumed by the backtester on the *next* candle's open to avoid look-ahead bias.
"""

from . import indicators as ind

# ── Bias normalization ─────────────────────────────────────────────────────────
# Map free-form bias strings (from templates or an LLM) onto a canonical generator.
_BIAS_ALIASES = {
    "scalper": "scalper", "long_scalper": "scalper", "short_scalper": "scalper",
    "scalping": "scalper", "hft": "scalper",
    "trend_following": "trend_following", "trend": "trend_following",
    "ema_crossover": "trend_following",
    "mean_reversion": "mean_reversion", "mean_rev": "mean_reversion",
    "reversal": "mean_reversion", "oversold_reversal": "mean_reversion",
    "breakout": "breakout", "breakout_momentum": "breakout",
    "long_only": "long_only", "bull_only": "long_only",
    "short_only": "short_only", "bear_only": "short_only",
    "volume_momentum": "volume_momentum", "volume_spike": "volume_momentum",
    "macd_momentum": "macd_momentum", "macd": "macd_momentum",
    "rsi_divergence": "rsi_divergence", "divergence": "rsi_divergence",
    "bollinger_squeeze": "bollinger_squeeze", "bb_squeeze": "bollinger_squeeze",
    "squeeze": "bollinger_squeeze",
    "stoch_rsi": "stoch_rsi", "stochastic_rsi": "stoch_rsi",
    "supertrend": "supertrend", "super_trend": "supertrend",
    "ema_cross_1h": "ema_cross_1h", "ema_1h": "ema_cross_1h",
    "heikin_ashi": "heikin_ashi", "ha": "heikin_ashi",
}


def normalize_bias(raw: str) -> str:
    """Resolve a free-form bias string to a canonical generator key."""
    b = (raw or "").lower()
    bias = _BIAS_ALIASES.get(b)
    if bias:
        return bias
    if "scalp" in b:                         return "scalper"
    if "macd" in b:                          return "macd_momentum"
    if "volume" in b:                        return "volume_momentum"
    if "break" in b:                         return "breakout"
    if "squeeze" in b or "bolling" in b:     return "bollinger_squeeze"
    if "diverg" in b:                        return "rsi_divergence"
    if "stoch" in b:                         return "stoch_rsi"
    if "super" in b:                         return "supertrend"
    if "heikin" in b or "_ha" in b:          return "heikin_ashi"
    if "1h" in b and "ema" in b:             return "ema_cross_1h"
    if "revers" in b or "mean_rev" in b:     return "mean_reversion"
    if "long" in b and "only" in b:          return "long_only"
    if "short" in b and "only" in b:         return "short_only"
    if "trend" in b or "ema" in b:           return "trend_following"
    return "trend_following"


# ── Generators ─────────────────────────────────────────────────────────────────

def trend_following(closes, highs, lows):
    """EMA 20/50 crossover."""
    fast, slow = ind.ema(closes, 20), ind.ema(closes, 50)
    signals = [0] * len(closes)
    for i in range(51, len(closes)):
        if None in (fast[i], slow[i], fast[i - 1], slow[i - 1]):
            continue
        if fast[i - 1] <= slow[i - 1] and fast[i] > slow[i]:
            signals[i] = 1
        elif fast[i - 1] >= slow[i - 1] and fast[i] < slow[i]:
            signals[i] = -1
    return signals


def mean_reversion(closes, highs, lows):
    """RSI extremes confirmed by Bollinger band touch."""
    rsi = ind.rsi(closes, 14)
    bb_u, _, bb_l = ind.bollinger(closes, 20, 2.0)
    signals = [0] * len(closes)
    for i in range(20, len(closes)):
        if rsi[i] is None or bb_l[i] is None:
            continue
        if rsi[i] < 32 and closes[i] <= bb_l[i] * 1.01:
            signals[i] = 1
        elif rsi[i] > 68 and closes[i] >= bb_u[i] * 0.99:
            signals[i] = -1
    return signals


def breakout(closes, highs, lows):
    """Donchian 20-period breakout."""
    dh, dl = ind.donchian_high(highs, 20), ind.donchian_low(lows, 20)
    signals = [0] * len(closes)
    for i in range(21, len(closes)):
        if dh[i - 1] is None or dl[i - 1] is None:
            continue
        if closes[i] > dh[i - 1] and closes[i - 1] <= dh[i - 1]:
            signals[i] = 1
        elif closes[i] < dl[i - 1] and closes[i - 1] >= dl[i - 1]:
            signals[i] = -1
    return signals


def long_only(closes, highs, lows):
    """RSI oversold bounce + bullish EMA structure. Longs only."""
    rsi = ind.rsi(closes, 14)
    ema20, ema50 = ind.ema(closes, 20), ind.ema(closes, 50)
    bb_u, _, bb_l = ind.bollinger(closes, 20, 2.0)
    signals = [0] * len(closes)
    for i in range(51, len(closes)):
        if rsi[i] is None or ema20[i] is None or ema50[i] is None:
            continue
        rsi_prev = rsi[i - 1] if rsi[i - 1] is not None else 50
        oversold_bounce = rsi_prev < 38 and rsi[i] > rsi_prev
        ema_bullish = ema20[i] > ema50[i]
        near_support = bb_l[i] is not None and closes[i] <= bb_l[i] * 1.015
        if oversold_bounce and (ema_bullish or near_support):
            signals[i] = 1
    return signals


def short_only(closes, highs, lows):
    """RSI overbought rejection + bearish EMA structure. Shorts only."""
    rsi = ind.rsi(closes, 14)
    ema20, ema50 = ind.ema(closes, 20), ind.ema(closes, 50)
    bb_u, _, bb_l = ind.bollinger(closes, 20, 2.0)
    signals = [0] * len(closes)
    for i in range(51, len(closes)):
        if rsi[i] is None or ema20[i] is None or ema50[i] is None:
            continue
        rsi_prev = rsi[i - 1] if rsi[i - 1] is not None else 50
        overbought_reject = rsi_prev > 63 and rsi[i] < rsi_prev
        ema_bearish = ema20[i] < ema50[i]
        near_resistance = bb_u[i] is not None and closes[i] >= bb_u[i] * 0.985
        if overbought_reject and (ema_bearish or near_resistance):
            signals[i] = -1
    return signals


def volume_momentum(closes, highs, lows, volumes, opens=None):
    """Volume spike + directional candle above/below EMA 50."""
    vma, ema50 = ind.volume_ma(volumes, 20), ind.ema(closes, 50)
    signals = [0] * len(closes)
    for i in range(51, len(closes)):
        if vma[i] is None or ema50[i] is None or vma[i] == 0:
            continue
        if volumes[i] <= vma[i] * 1.5:
            continue
        candle_range = highs[i] - lows[i]
        if candle_range == 0:
            continue
        open_price = opens[i] if opens is not None else closes[i - 1]
        if abs(closes[i] - open_price) / candle_range <= 0.2:
            continue
        if closes[i] > ema50[i] and closes[i] > closes[i - 1]:
            signals[i] = 1
        elif closes[i] < ema50[i] and closes[i] < closes[i - 1]:
            signals[i] = -1
    return signals


def macd_momentum(closes, highs, lows):
    """MACD/signal crossover gated by RSI to avoid extremes."""
    macd_line, signal_line, _ = ind.macd(closes, 12, 26, 9)
    rsi = ind.rsi(closes, 14)
    signals = [0] * len(closes)
    for i in range(35, len(closes)):
        if None in (macd_line[i], signal_line[i], macd_line[i - 1], signal_line[i - 1]):
            continue
        r = rsi[i] if rsi[i] is not None else 50
        bull = macd_line[i - 1] <= signal_line[i - 1] and macd_line[i] > signal_line[i]
        bear = macd_line[i - 1] >= signal_line[i - 1] and macd_line[i] < signal_line[i]
        if bull and 35 < r < 68:
            signals[i] = 1
        elif bear and 32 < r < 65:
            signals[i] = -1
    return signals


def rsi_divergence(closes, highs, lows):
    """Price/RSI divergence over a 20-candle lookback."""
    rsi = ind.rsi(closes, 14)
    signals = [0] * len(closes)
    lookback = 20
    for i in range(lookback + 10, len(closes)):
        if rsi[i] is None or rsi[i - 10] is None:
            continue
        price_old_low = min(closes[i - lookback: i - 10])
        price_old_high = max(closes[i - lookback: i - 10])
        price_new_low = min(closes[i - 10: i + 1])
        price_new_high = max(closes[i - 10: i + 1])
        rsi_old, rsi_now = rsi[i - 10], rsi[i]
        if price_new_low < price_old_low and rsi_now > rsi_old and rsi_now < 45:
            signals[i] = 1
        elif price_new_high > price_old_high and rsi_now < rsi_old and rsi_now > 55:
            signals[i] = -1
    return signals


def bollinger_squeeze(closes, highs, lows):
    """Volatility squeeze release: compressed bandwidth then directional break."""
    bb_u, bb_m, bb_l = ind.bollinger(closes, 20, 2.0)
    ema50 = ind.ema(closes, 50)
    signals = [0] * len(closes)
    for i in range(51, len(closes)):
        if None in (bb_u[i], bb_m[i], bb_l[i]) or bb_m[i] == 0:
            continue
        bw_now = (bb_u[i] - bb_l[i]) / bb_m[i]
        bw_window = [
            (bb_u[j] - bb_l[j]) / bb_m[j]
            for j in range(max(0, i - 25), i - 5)
            if bb_u[j] is not None and bb_m[j] is not None and bb_m[j] > 0
        ]
        if len(bw_window) < 10:
            continue
        bw_avg = sum(bw_window) / len(bw_window)
        bw_prev = None
        if bb_u[i - 1] is not None and bb_m[i - 1] is not None and bb_m[i - 1] > 0:
            bw_prev = (bb_u[i - 1] - bb_l[i - 1]) / bb_m[i - 1]
        was_squeeze = bw_prev is not None and bw_prev < bw_avg * 0.7
        is_squeeze = bw_now < bw_avg * 0.7
        if was_squeeze and not is_squeeze and ema50[i] is not None:
            if closes[i] > bb_m[i] and closes[i] > ema50[i]:
                signals[i] = 1
            elif closes[i] < bb_m[i] and closes[i] < ema50[i]:
                signals[i] = -1
    return signals


def stoch_rsi(closes, highs, lows):
    """Stochastic RSI crossing out of extreme zones."""
    rsi_series = ind.rsi(closes, 14)
    rsi_clean = [(i, v) for i, v in enumerate(rsi_series) if v is not None]
    if len(rsi_clean) < 20:
        return [0] * len(closes)

    stoch_k, period = {}, 14
    for idx in range(period, len(rsi_clean)):
        window = [v for _, v in rsi_clean[idx - period: idx + 1]]
        lo, hi = min(window), max(window)
        k = (window[-1] - lo) / (hi - lo) * 100 if hi > lo else 50.0
        stoch_k[rsi_clean[idx][0]] = k

    signals = [0] * len(closes)
    keys = sorted(stoch_k.keys())
    for i in range(1, len(keys)):
        cur, prev = keys[i], keys[i - 1]
        if stoch_k[prev] < 20 and stoch_k[cur] >= 20:
            signals[cur] = 1
        elif stoch_k[prev] > 80 and stoch_k[cur] <= 80:
            signals[cur] = -1
    return signals


def supertrend(closes, highs, lows, atr_period: int = 14, mult: float = 3.0):
    """
    SuperTrend(14, 3). Signals fire when the trend direction flips. Uses proper
    trailing final upper/lower bands so direction actually changes over time.
    """
    n = len(closes)
    if n <= atr_period:
        return [0] * n

    atr = ind.atr(highs, lows, closes, atr_period)
    hl2 = [(highs[i] + lows[i]) / 2 for i in range(n)]

    final_ub = [None] * n
    final_lb = [None] * n
    direction = [0] * n  # +1 uptrend, -1 downtrend
    signals = [0] * n

    start = next((i for i, v in enumerate(atr) if v is not None), None)
    if start is None:
        return signals

    final_ub[start] = hl2[start] + mult * atr[start]
    final_lb[start] = hl2[start] - mult * atr[start]
    direction[start] = 1

    for i in range(start + 1, n):
        basic_ub = hl2[i] + mult * atr[i]
        basic_lb = hl2[i] - mult * atr[i]

        final_ub[i] = (basic_ub if (basic_ub < final_ub[i - 1] or closes[i - 1] > final_ub[i - 1])
                       else final_ub[i - 1])
        final_lb[i] = (basic_lb if (basic_lb > final_lb[i - 1] or closes[i - 1] < final_lb[i - 1])
                       else final_lb[i - 1])

        if direction[i - 1] == 1:
            direction[i] = -1 if closes[i] < final_lb[i] else 1
        else:
            direction[i] = 1 if closes[i] > final_ub[i] else -1

        if direction[i] == 1 and direction[i - 1] == -1:
            signals[i] = 1
        elif direction[i] == -1 and direction[i - 1] == 1:
            signals[i] = -1
    return signals


def ema_cross_1h(closes, highs, lows):
    """Faster EMA 9/21 crossover gated by RSI."""
    ema9, ema21 = ind.ema(closes, 9), ind.ema(closes, 21)
    rsi = ind.rsi(closes, 14)
    signals = [0] * len(closes)
    for i in range(22, len(closes)):
        if None in (ema9[i], ema21[i], ema9[i - 1], ema21[i - 1]):
            continue
        r = rsi[i] if rsi[i] is not None else 50
        bull = ema9[i - 1] <= ema21[i - 1] and ema9[i] > ema21[i]
        bear = ema9[i - 1] >= ema21[i - 1] and ema9[i] < ema21[i]
        if bull and 38 < r < 65:
            signals[i] = 1
        elif bear and 35 < r < 62:
            signals[i] = -1
    return signals


def heikin_ashi(closes, highs, lows, opens=None):
    """Three consecutive Heikin-Ashi candles after an opposite one."""
    if opens is None:
        opens = [closes[0]] + closes[:-1]
    ha_close = [(opens[i] + highs[i] + lows[i] + closes[i]) / 4 for i in range(len(closes))]
    ha_open = [ha_close[0]]
    for i in range(1, len(closes)):
        ha_open.append((ha_open[i - 1] + ha_close[i - 1]) / 2)
    rsi = ind.rsi(closes, 14)
    signals = [0] * len(closes)
    for i in range(5, len(closes)):
        r = rsi[i] if rsi[i] is not None else 50
        ha_bull_3 = all(ha_close[j] > ha_open[j] for j in (i - 2, i - 1, i))
        ha_bear_3 = all(ha_close[j] < ha_open[j] for j in (i - 2, i - 1, i))
        prev_bear = ha_close[i - 3] < ha_open[i - 3]
        prev_bull = ha_close[i - 3] > ha_open[i - 3]
        if ha_bull_3 and prev_bear and r < 65:
            signals[i] = 1
        elif ha_bear_3 and prev_bull and r > 35:
            signals[i] = -1
    return signals


def scalper(closes, highs, lows):
    """Fast EMA 5/15 crossover in the neutral RSI zone."""
    ema5, ema15 = ind.ema(closes, 5), ind.ema(closes, 15)
    rsi = ind.rsi(closes, 7)
    signals = [0] * len(closes)
    for i in range(16, len(closes)):
        if None in (ema5[i], ema15[i], ema5[i - 1], ema15[i - 1]):
            continue
        r = rsi[i] if rsi[i] is not None else 50
        bull = ema5[i - 1] <= ema15[i - 1] and ema5[i] > ema15[i]
        bear = ema5[i - 1] >= ema15[i - 1] and ema5[i] < ema15[i]
        if bull and 38 < r < 65:
            signals[i] = 1
        elif bear and 35 < r < 62:
            signals[i] = -1
    return signals


def generate(bias: str, closes, highs, lows, volumes=None, opens=None):
    """Dispatch to the generator for a (normalized) bias."""
    b = normalize_bias(bias)
    if b == "mean_reversion":     return mean_reversion(closes, highs, lows)
    if b == "breakout":           return breakout(closes, highs, lows)
    if b == "long_only":          return long_only(closes, highs, lows)
    if b == "short_only":         return short_only(closes, highs, lows)
    if b == "volume_momentum":    return volume_momentum(closes, highs, lows, volumes or [], opens)
    if b == "macd_momentum":      return macd_momentum(closes, highs, lows)
    if b == "scalper":            return scalper(closes, highs, lows)
    if b == "rsi_divergence":     return rsi_divergence(closes, highs, lows)
    if b == "bollinger_squeeze":  return bollinger_squeeze(closes, highs, lows)
    if b == "stoch_rsi":          return stoch_rsi(closes, highs, lows)
    if b == "supertrend":         return supertrend(closes, highs, lows)
    if b == "ema_cross_1h":       return ema_cross_1h(closes, highs, lows)
    if b == "heikin_ashi":        return heikin_ashi(closes, highs, lows, opens)
    return trend_following(closes, highs, lows)
