"""
Strategy templates — build a backtestable strategy spec for a (token, bias) pair.

A spec is a plain dict the backtester understands plus human-readable entry/exit
rules and a rationale, so the final output is self-documenting. SL/TP defaults per
bias are empirically reasonable starting points; the architect scales them by ATR.
"""

from datetime import datetime, timezone

# Default SL/TP/leverage per bias, and the timeframe each bias is designed for.
BIAS_PARAMS = {
    "trend_following":   {"sl": 2.5, "tp": 6.0, "tf": "4h"},
    "mean_reversion":    {"sl": 1.5, "tp": 3.5, "tf": "4h"},
    "breakout":          {"sl": 2.0, "tp": 5.0, "tf": "4h"},
    "long_only":         {"sl": 2.0, "tp": 5.0, "tf": "4h"},
    "short_only":        {"sl": 2.0, "tp": 5.0, "tf": "4h"},
    "volume_momentum":   {"sl": 2.0, "tp": 6.0, "tf": "4h"},
    "macd_momentum":     {"sl": 2.0, "tp": 6.0, "tf": "4h"},
    "scalper":           {"sl": 1.5, "tp": 4.0, "tf": "15m"},
    "rsi_divergence":    {"sl": 1.8, "tp": 5.0, "tf": "4h"},
    "bollinger_squeeze": {"sl": 2.0, "tp": 6.0, "tf": "4h"},
    "stoch_rsi":         {"sl": 1.8, "tp": 4.5, "tf": "4h"},
    "ema_cross_1h":      {"sl": 1.5, "tp": 4.0, "tf": "1h"},
    "heikin_ashi":       {"sl": 2.0, "tp": 5.5, "tf": "4h"},
}

# Human-readable name, entry rules, exit rules per bias.
_DESCRIPTIONS = {
    "trend_following": ("EMA Trend", [
        "EMA 20 crosses above EMA 50 with price above EMA 200 (long)",
        "EMA 20 crosses below EMA 50 with price below EMA 200 (short)"],
        "EMA 20/50 crossover with an EMA 200 macro filter."),
    "mean_reversion": ("RSI Mean Reversion", [
        "RSI 14 < 32 and price at lower Bollinger band (long)",
        "RSI 14 > 68 and price at upper Bollinger band (short)"],
        "Fades RSI extremes confirmed by Bollinger band touches. Best in ranges."),
    "breakout": ("Donchian Breakout", [
        "Close breaks above the 20-period Donchian high (long)",
        "Close breaks below the 20-period Donchian low (short)"],
        "Captures post-consolidation breakouts via Donchian channels."),
    "long_only": ("Bull Momentum", [
        "RSI bounces from oversold with bullish EMA structure (long only)"],
        "Long-only oversold bounces in confirmed uptrends."),
    "short_only": ("Bear Momentum", [
        "RSI rejects from overbought with bearish EMA structure (short only)"],
        "Short-only overbought rejections in confirmed downtrends."),
    "volume_momentum": ("Volume Momentum", [
        "Volume > 1.5x its 20-period average on a directional candle",
        "Price closes above EMA 50 (long) or below (short)"],
        "Volume spikes confirm participation; EMA 50 sets direction."),
    "macd_momentum": ("MACD Momentum", [
        "MACD crosses above signal with RSI 35-68 (long)",
        "MACD crosses below signal with RSI 32-65 (short)"],
        "MACD/signal crossovers gated by RSI to avoid extremes."),
    "scalper": ("Fast Scalper", [
        "EMA 5 crosses EMA 15 in the neutral RSI zone"],
        "Fast EMA 5/15 crossover for short timeframes."),
    "rsi_divergence": ("RSI Divergence", [
        "Price lower-low while RSI higher-low, RSI < 45 (long)",
        "Price higher-high while RSI lower-high, RSI > 55 (short)"],
        "Trades momentum exhaustion when price and RSI diverge."),
    "bollinger_squeeze": ("Bollinger Squeeze", [
        "Bandwidth compressed < 70% of its 25-bar average, then a directional break"],
        "Detects volatility compression preceding explosive moves."),
    "stoch_rsi": ("Stochastic RSI", [
        "Stoch RSI %K crosses up out of <20 (long) or down out of >80 (short)"],
        "More sensitive than raw RSI; trades exits from extreme zones."),
    "ema_cross_1h": ("EMA 9/21 Cross", [
        "EMA 9 crosses EMA 21 with RSI in the neutral zone"],
        "Faster EMA crossover tuned for the 1h timeframe."),
    "heikin_ashi": ("Heikin Ashi Trend", [
        "Three consecutive HA candles in one direction after an opposite candle"],
        "Smoothed candles filter noise to ride clean trends."),
}

ALL_BIASES = list(BIAS_PARAMS.keys())


def build_spec(token: str, bias: str, atr_pct: float = 2.0, regime: str = "unknown",
               timeframe: str = None) -> dict:
    """Build one backtestable strategy spec for a token and bias."""
    params = dict(BIAS_PARAMS.get(bias, BIAS_PARAMS["trend_following"]))
    tf = timeframe or params["tf"]
    sl, tp = params["sl"], params["tp"]

    # Widen stops in high volatility, tighten in low — keeps risk proportional to ATR.
    if atr_pct > 3.0:
        sl, tp = round(sl * 1.2, 1), round(tp * 1.2, 1)
    elif atr_pct < 1.0:
        sl, tp = round(sl * 0.9, 1), round(tp * 0.9, 1)

    name, entry_rules, rationale = _DESCRIPTIONS.get(
        bias, _DESCRIPTIONS["trend_following"])
    ticker = token.upper().replace("USDT", "")

    return {
        "strategy_name": f"{name} {ticker} {tf}",
        "token": ticker,
        "timeframe": tf,
        "directional_bias": bias,
        "stop_loss_pct": sl,
        "take_profit_pct": tp,
        "entry_rules": entry_rules,
        "exit_rules": [
            f"Take profit at +{tp}% or stop loss at -{sl}%",
            "Exit on opposite signal from the same generator",
        ],
        "rationale": f"{rationale} Regime: {regime}, ATR {atr_pct:.1f}%.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
