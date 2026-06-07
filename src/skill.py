"""
CMC Quant Panel — Skill entry point.

Pipeline: CMC intelligence -> Market Scout -> Architects -> Backtester ->
Risk/Devil/Voting -> Arbitrator. Produces a backtestable strategy spec, a full
backtest report, and a transparent panel verdict for any token.

Usage:
    python -m src.skill --token BTC
    python -m src.skill --token ETH --timeframe 4h --json out.json
"""

import argparse
import json
import sys

from . import config
from .cmc import client as cmc
from .data.ohlcv import fetch_ohlcv
from .engine import backtester
from .panel import scout, architects, risk, devil, voting, arbitrator


def run_skill(token: str, timeframe: str = None, days: int = None) -> dict:
    """Run the full Skill pipeline for a token and return the structured result."""
    cfg = config.load()
    days = days or cfg.get("backtest", {}).get("days", 730)
    provider = cfg.get("ohlcv_provider", "binance")

    cmc_intel = cmc.intelligence(token)
    brief = scout.analyze(token, fetch_ohlcv(token, timeframe or "4h", days, provider), cmc_intel)

    specs = architects.propose(brief)
    candidates = []
    for spec in specs:
        tf = timeframe or spec["timeframe"]
        spec["timeframe"] = tf
        candles = fetch_ohlcv(token, tf, days, provider)
        bt = backtester.full_backtest(candles, spec)
        assessment = risk.assess(spec, bt)
        audit = risk.audit(spec, bt)
        dev = devil.review(spec, bt, brief)
        v = voting.vote(bt, audit, dev)
        candidates.append({
            "strategy": spec, "backtest": bt, "assessment": assessment,
            "audit": audit, "devil": dev, "vote": v,
        })

    decision = arbitrator.decide(candidates)
    return {
        "token": token.upper(),
        "cmc_intelligence": cmc_intel,
        "market_brief": brief,
        "candidates_evaluated": len(candidates),
        "decision": decision,
    }


# ── Report formatting ──────────────────────────────────────────────────────────

def format_report(result: dict) -> str:
    brief = result["market_brief"]
    dec = result["decision"]
    snap = brief["snapshot"]
    sent = brief["sentiment"]
    lines = []

    lines.append("=" * 70)
    lines.append(f"  CMC QUANT PANEL — second opinion for {result['token']}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Regime: {brief['regime']}   |   {brief['narrative']}")
    lines.append(f"Technicals: price {snap['price']}  RSI {snap['rsi_14']}  "
                 f"ATR {snap['atr_pct']}%  trend {snap['trend']}")
    fg = sent.get("fear_greed")
    if fg is not None:
        lines.append(f"Sentiment:  Fear&Greed {fg}/100 ({sent['fear_greed_label']})  "
                     f"7d {sent.get('change_7d')}%  30d {sent.get('change_30d')}%")
    lines.append("")
    lines.append(f"Candidates evaluated: {result['candidates_evaluated']}  "
                 f"(audit-approved: {dec['approved_count']})")
    lines.append("")
    lines.append("RANKING")
    lines.append(f"  {'strategy':<26}{'score':>7}{'avg/mo%':>9}{'sharpe':>8}{'audit':>11}{'panel':>8}")
    for r in dec["ranking"]:
        lines.append(f"  {r['strategy_name'][:25]:<26}{r['score']:>7}"
                     f"{r['avg_monthly_return']:>9}{r['sharpe']:>8}"
                     f"{r['audit']:>11}{r['consensus']:>8}")
    lines.append("")

    winner = dec.get("winner")
    if winner and winner["audit"]["verdict"] == "APPROVED":
        s, bt, v = winner["strategy"], winner["backtest"], winner["vote"]
        lines.append("-" * 70)
        lines.append(f"  WINNER: {s['strategy_name']}")
        lines.append("-" * 70)
        lines.append(f"  Bias: {s['directional_bias']}   SL/TP: -{s['stop_loss_pct']}% / "
                     f"+{s['take_profit_pct']}%   TF: {s['timeframe']}")
        lines.append(f"  Backtest ({bt['candles_used']} candles): "
                     f"{bt['avg_monthly_return']}%/mo, WR {bt['win_rate']}%, "
                     f"maxDD {bt['max_drawdown']}%, Sharpe {bt['sharpe']}, "
                     f"PF {bt['profit_factor']}, {bt['total_trades']} trades")
        wf = bt.get("walk_forward", {})
        lines.append(f"  Walk-forward: {wf.get('verdict')} "
                     f"(IS {wf.get('in_sample_return')}%/mo, OOS {wf.get('out_sample_return')}%/mo)")
        last = bt.get("last_90d", {})
        lines.append(f"  Last 90d: {last.get('avg_monthly_return')}%/mo, "
                     f"WR {last.get('win_rate')}%, {last.get('total_trades')} trades")
        lines.append(f"  Entry: {'; '.join(s['entry_rules'])}")
        lines.append(f"  Devil's Advocate: {winner['devil']['risk_flag']} — "
                     f"{winner['devil']['concerns'][0]}")
        lines.append("")
        lines.append(f"  Panel: {v['label']} "
                     f"(DEPLOY {v['tally']['DEPLOY']} / NEEDS_WORK {v['tally']['NEEDS_WORK']} "
                     f"/ SKIP {v['tally']['SKIP']}), avg confidence {v['avg_confidence']}/10")
    else:
        lines.append("-" * 70)
        lines.append(f"  VERDICT: {dec['verdict']}")
        lines.append(f"  {dec['summary']}")
    lines.append("")
    lines.append(f"=> {dec['summary']}")
    return "\n".join(lines)


def main(argv=None):
    # Ensure UTF-8 output so em-dashes etc. render on Windows consoles (cp1252 default).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    p = argparse.ArgumentParser(description="CMC Quant Panel - backtestable strategy Skill")
    p.add_argument("--token", required=True, help="Token symbol, e.g. BTC, ETH, BNB, SOL")
    p.add_argument("--timeframe", default=None, help="Override timeframe (15m,1h,4h,1d)")
    p.add_argument("--days", type=int, default=None, help="History window in days")
    p.add_argument("--json", dest="json_out", default=None, help="Write full result JSON to this path")
    args = p.parse_args(argv)

    try:
        result = run_skill(args.token, args.timeframe, args.days)
    except ValueError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 2

    print(format_report(result))

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nFull result written to {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
