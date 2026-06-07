"""
Agent: Voting Panel.

Eight specialist personas each cast a transparent vote — DEPLOY / SKIP /
NEEDS_WORK — with a justification. This is the "second opinion": instead of one
opaque score, you see a panel reach a consensus you can interrogate.
"""

VOTERS = [
    ("Market Scout",        "market regime & timing"),
    ("Strategy Architect A", "trend-following design"),
    ("Strategy Architect B", "breakout & momentum design"),
    ("Strategy Architect C", "mean-reversion design"),
    ("Risk Assessor",        "leverage & exposure"),
    ("Backtester",           "statistical validation"),
    ("Risk Auditor",         "minimum criteria compliance"),
    ("Devil's Advocate",     "downside & failure modes"),
]


def vote(backtest: dict, audit: dict, devil: dict) -> dict:
    """Run the panel and tally a consensus for one strategy."""
    votes = [_cast(name, role, backtest, audit, devil) for name, role in VOTERS]

    deploy = sum(1 for v in votes if v["vote"] == "DEPLOY")
    skip = sum(1 for v in votes if v["vote"] == "SKIP")
    needs = sum(1 for v in votes if v["vote"] == "NEEDS_WORK")
    avg_conf = round(sum(v["confidence"] for v in votes) / len(votes), 1)

    if deploy >= 5:
        consensus, label = "DEPLOY", "Consensus DEPLOY"
    elif skip >= 5:
        consensus, label = "SKIP", "Consensus SKIP"
    else:
        consensus, label = "MIXED", "Split vote"

    return {
        "agent": "Voting Panel",
        "votes": votes,
        "tally": {"DEPLOY": deploy, "SKIP": skip, "NEEDS_WORK": needs},
        "consensus": consensus,
        "label": label,
        "avg_confidence": avg_conf,
    }


def _cast(name: str, role: str, backtest: dict, audit: dict, devil: dict) -> dict:
    """One persona's reasoned vote. Deterministic from the evidence."""
    avg_monthly = backtest.get("avg_monthly_return", 0)
    max_dd = backtest.get("max_drawdown", 0)
    win_rate = backtest.get("win_rate", 0)
    flag = devil.get("risk_flag", "MEDIUM")

    if audit.get("verdict") == "REJECTED":
        return {"voter": name, "role": role, "vote": "SKIP", "confidence": 9,
                "justification": f"Rejected by audit: {audit.get('reason', '?')}"}
    if flag == "HIGH":
        return {"voter": name, "role": role, "vote": "SKIP", "confidence": 8,
                "justification": "Devil's Advocate flagged HIGH risk."}
    if avg_monthly >= 5 and max_dd < 25 and win_rate >= 35:
        return {"voter": name, "role": role, "vote": "DEPLOY", "confidence": 7,
                "justification": f"Solid: {avg_monthly:.1f}%/mo, DD {max_dd:.1f}%, WR {win_rate:.1f}%."}
    if avg_monthly >= 2:
        return {"voter": name, "role": role, "vote": "NEEDS_WORK", "confidence": 6,
                "justification": "Marginal edge — monitor and refine before sizing up."}
    return {"voter": name, "role": role, "vote": "SKIP", "confidence": 7,
            "justification": "Return insufficient for the risk taken."}
