"""
Agent: Strategy Architects.

Turn the scout's market brief into concrete, backtestable strategy specs — one
per recommended bias, with SL/TP scaled to current volatility. These are the
candidates the backtester and the rest of the panel will scrutinize.
"""

from ..engine import templates


def propose(scout_brief: dict, max_candidates: int = 6) -> list:
    """Build candidate strategy specs from the scout's recommended biases."""
    token = scout_brief.get("token", "BTC")
    regime = scout_brief.get("regime", "unknown")
    snap = scout_brief.get("snapshot", {})
    atr = snap.get("atr_pct", 2.0)

    biases = scout_brief.get("recommended_biases", [])[:max_candidates]
    specs = []
    for bias in biases:
        if bias not in templates.BIAS_PARAMS:
            continue
        specs.append(templates.build_spec(token, bias, atr_pct=atr, regime=regime))
    return specs
