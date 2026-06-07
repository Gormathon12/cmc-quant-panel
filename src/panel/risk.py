"""
Agents: Risk Assessor + Risk Auditor.

The assessor sizes leverage from realized volatility and drawdown. The auditor
applies hard minimum criteria a strategy must clear to be deployable — the
gate that keeps junk specs out regardless of a flattering headline return.
"""

# Minimum bar a strategy must clear to pass the audit.
MIN_TRADES = 10
MAX_DRAWDOWN = 40.0       # %
MIN_AVG_MONTHLY = 1.0     # %
MIN_WIN_RATE = 25.0       # %


def assess(strategy: dict, backtest: dict) -> dict:
    """Recommend leverage and summarize the risk profile of a strategy."""
    atr_implied = strategy.get("stop_loss_pct", 2.0)
    max_dd = backtest.get("max_drawdown", 0)

    if max_dd > 30 or atr_implied > 3.0:
        leverage = 2
    elif max_dd > 20:
        leverage = 3
    else:
        leverage = 3

    return {
        "agent": "Risk Assessor",
        "recommended_leverage": leverage,
        "max_drawdown": max_dd,
        "sharpe": backtest.get("sharpe", 0),
        "risk_note": _risk_note(max_dd, backtest.get("sharpe", 0)),
    }


def _risk_note(max_dd: float, sharpe: float) -> str:
    if max_dd > 35:
        return "High drawdown — only with strict position sizing."
    if sharpe >= 2.0:
        return "Strong risk-adjusted returns."
    if sharpe >= 1.0:
        return "Acceptable risk-adjusted returns."
    return "Weak risk-adjusted returns — caution."


def audit(strategy: dict, backtest: dict) -> dict:
    """Hard pass/fail gate against minimum deployability criteria."""
    reasons = []
    trades = backtest.get("total_trades", 0)
    max_dd = backtest.get("max_drawdown", 0)
    avg_monthly = backtest.get("avg_monthly_return", 0)
    win_rate = backtest.get("win_rate", 0)
    wf = backtest.get("walk_forward", {})
    recent = backtest.get("last_90d", {})

    if trades < MIN_TRADES:
        reasons.append(f"Too few trades ({trades} < {MIN_TRADES}) — not significant")
    if max_dd > MAX_DRAWDOWN:
        reasons.append(f"Drawdown too high ({max_dd}% > {MAX_DRAWDOWN}%)")
    if avg_monthly < MIN_AVG_MONTHLY:
        reasons.append(f"Return too low ({avg_monthly}%/mo < {MIN_AVG_MONTHLY}%)")
    if win_rate < MIN_WIN_RATE:
        reasons.append(f"Win rate too low ({win_rate}% < {MIN_WIN_RATE}%)")
    if wf.get("verdict") in ("overfitting_suspected", "insufficient_signal"):
        reasons.append(f"Walk-forward failed: {wf.get('verdict')}")
    if recent.get("avg_monthly_return", 0) < -2.0:
        reasons.append("Losing money over the last 90 days — edge may be gone")

    verdict = "REJECTED" if reasons else "APPROVED"
    return {
        "agent": "Risk Auditor",
        "verdict": verdict,
        "reason": "; ".join(reasons) if reasons else "Meets all minimum criteria",
    }
