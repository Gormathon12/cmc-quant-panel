"""
Agent: Market Scout.

Fuses CoinMarketCap intelligence (momentum, sentiment, global regime) with the
technical snapshot from historical candles to classify the market regime and
recommend which strategy families fit current conditions. This is what makes the
strategy generation *data-driven* rather than blind.
"""

from ..engine import indicators


def analyze(token: str, candles: list, cmc_intel: dict) -> dict:
    """Return a market brief: regime, snapshot, sentiment, and recommended biases."""
    snap = indicators.snapshot(candles)
    quote = cmc_intel.get("quote", {})
    fg = cmc_intel.get("fear_greed", {})
    glob = cmc_intel.get("global", {})

    regime = _classify_regime(snap, quote, fg)
    recommended = _recommend_biases(regime, snap)

    return {
        "agent": "Market Scout",
        "token": token.upper(),
        "regime": regime,
        "snapshot": snap,
        "sentiment": {
            "fear_greed": fg.get("value"),
            "fear_greed_label": fg.get("classification"),
            "change_24h": quote.get("percent_change_24h"),
            "change_7d": quote.get("percent_change_7d"),
            "change_30d": quote.get("percent_change_30d"),
        },
        "market": {
            "btc_dominance": glob.get("btc_dominance"),
            "total_cap_change_24h": glob.get("total_market_cap_change_24h"),
            "cmc_rank": quote.get("cmc_rank"),
        },
        "recommended_biases": recommended,
        "narrative": _narrative(token, regime, snap, fg, quote),
    }


def _classify_regime(snap: dict, quote: dict, fg: dict) -> str:
    """Combine technical trend, volatility and sentiment into a single regime label."""
    trend = snap.get("trend", "ranging")
    atr = snap.get("atr_pct", 2.0)
    rsi = snap.get("rsi_14", 50.0)
    fg_val = fg.get("value")

    if "strong" in trend:
        return "trending"
    if atr > 3.5:
        return "high_volatility"
    if atr < 1.2:
        return "low_volatility"
    if rsi > 65 or rsi < 35:
        return "trending"
    if fg_val is not None and (fg_val <= 20 or fg_val >= 80):
        return "sentiment_extreme"
    return "ranging"


# Which strategy families historically fit each regime. Ordered by preference.
_REGIME_BIASES = {
    "trending":          ["trend_following", "supertrend", "macd_momentum",
                          "heikin_ashi", "volume_momentum"],
    "high_volatility":   ["breakout", "volume_momentum", "bollinger_squeeze",
                          "macd_momentum"],
    "low_volatility":    ["mean_reversion", "stoch_rsi", "bollinger_squeeze",
                          "rsi_divergence"],
    "sentiment_extreme": ["rsi_divergence", "mean_reversion", "stoch_rsi",
                          "long_only"],
    "ranging":           ["mean_reversion", "stoch_rsi", "rsi_divergence",
                          "ema_cross_1h", "heikin_ashi"],
}


def _recommend_biases(regime: str, snap: dict) -> list:
    """Pick candidate biases for the regime, biased long/short by trend direction."""
    biases = list(_REGIME_BIASES.get(regime, _REGIME_BIASES["ranging"]))
    trend = snap.get("trend", "ranging")
    if "uptrend" in trend and "long_only" not in biases:
        biases.append("long_only")
    if "downtrend" in trend and "short_only" not in biases:
        biases.append("short_only")
    return biases


def _narrative(token, regime, snap, fg, quote) -> str:
    parts = [
        f"{token.upper()} is in a {regime.replace('_', ' ')} regime "
        f"(RSI {snap.get('rsi_14')}, ATR {snap.get('atr_pct')}%, trend {snap.get('trend')})."
    ]
    if fg.get("value") is not None:
        parts.append(f"Market sentiment: {fg.get('classification')} ({fg.get('value')}/100).")
    c7 = quote.get("percent_change_7d")
    if c7 is not None:
        parts.append(f"7-day move {c7:+.1f}%.")
    return " ".join(parts)
