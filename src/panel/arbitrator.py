"""
Agent: Arbitrator.

Ranks all reviewed candidates and selects the winner. Scoring rewards
risk-adjusted return and panel consensus, and hard-penalizes anything the audit
rejected — so a flashy but unsound strategy never wins.
"""


def _score(candidate: dict) -> float:
    bt = candidate["backtest"]
    vote = candidate["vote"]
    audit = candidate["audit"]

    if audit.get("verdict") == "REJECTED":
        return -1000.0 + bt.get("sharpe", 0)  # keep a stable relative order

    sharpe = bt.get("sharpe", 0)
    avg_monthly = bt.get("avg_monthly_return", 0)
    consistency = bt.get("walk_forward", {}).get("consistency_score", 0)
    recent = bt.get("last_90d", {}).get("avg_monthly_return", 0)
    deploy_votes = vote.get("tally", {}).get("DEPLOY", 0)

    return round(
        sharpe * 2.0
        + avg_monthly * 0.5
        + consistency * 3.0
        + recent * 0.3
        + deploy_votes * 1.0,
        3,
    )


def decide(candidates: list) -> dict:
    """Rank candidates and return the winner plus the full ranking."""
    ranked = sorted(candidates, key=_score, reverse=True)
    for c in ranked:
        c["arbitrator_score"] = _score(c)

    winner = ranked[0] if ranked else None
    approved = [c for c in ranked if c["audit"].get("verdict") == "APPROVED"]

    if not winner or winner["audit"].get("verdict") == "REJECTED":
        verdict = "NO_VIABLE_STRATEGY"
        summary = "No candidate cleared the risk audit. Best to wait for clearer conditions."
    else:
        verdict = winner["vote"]["consensus"]
        summary = (
            f"Top pick: {winner['strategy']['strategy_name']} — "
            f"{winner['backtest']['avg_monthly_return']}%/mo, "
            f"Sharpe {winner['backtest']['sharpe']}, "
            f"panel {winner['vote']['label'].lower()}."
        )

    return {
        "agent": "Arbitrator",
        "verdict": verdict,
        "summary": summary,
        "winner": winner,
        "approved_count": len(approved),
        "ranking": [
            {
                "strategy_name": c["strategy"]["strategy_name"],
                "bias": c["strategy"]["directional_bias"],
                "score": c["arbitrator_score"],
                "avg_monthly_return": c["backtest"]["avg_monthly_return"],
                "sharpe": c["backtest"]["sharpe"],
                "audit": c["audit"]["verdict"],
                "consensus": c["vote"]["consensus"],
            }
            for c in ranked
        ],
    }
