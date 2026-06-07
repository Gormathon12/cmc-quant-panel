"""
Agent: Devil's Advocate.

Actively argues against each strategy: surfaces overfitting, fragile trade counts,
regime mismatch and recency decay, then assigns a risk flag. A deliberate
counterweight to optimistic backtest headlines.
"""


def review(strategy: dict, backtest: dict, scout_brief: dict) -> dict:
    """Return concerns and a risk flag (LOW / MEDIUM / HIGH) for a strategy."""
    concerns = []
    wf = backtest.get("walk_forward", {})
    recent = backtest.get("last_90d", {})
    trades = backtest.get("total_trades", 0)
    max_dd = backtest.get("max_drawdown", 0)

    consistency = wf.get("consistency_score", 0)
    if wf.get("verdict") == "overfitting_suspected":
        concerns.append("Out-of-sample collapses vs in-sample — likely overfit.")
    elif consistency < 0.3:
        concerns.append(f"Low walk-forward consistency ({consistency}).")

    if trades < 20:
        concerns.append(f"Only {trades} trades — thin statistical basis.")
    if max_dd > 30:
        concerns.append(f"Deep {max_dd}% drawdown could wipe undercapitalized accounts.")
    if recent.get("avg_monthly_return", 0) < 0:
        concerns.append("Negative returns in the last 90 days.")

    regime = scout_brief.get("regime", "")
    bias = strategy.get("directional_bias", "")
    if regime == "trending" and bias == "mean_reversion":
        concerns.append("Mean-reversion in a trending regime fights the tape.")
    if regime in ("ranging", "low_volatility") and bias in ("breakout", "trend_following"):
        concerns.append("Trend/breakout in a flat regime invites whipsaws.")

    if len(concerns) >= 3:
        flag = "HIGH"
    elif len(concerns) >= 1:
        flag = "MEDIUM"
    else:
        flag = "LOW"

    return {
        "agent": "Devil's Advocate",
        "risk_flag": flag,
        "concerns": concerns or ["No material concerns identified."],
    }
