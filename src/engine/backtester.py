"""
Backtesting engine — runs a strategy spec over historical OHLCV.

Design choices that keep results honest:
  * No look-ahead: a signal on candle i is acted on at candle i+1's open.
  * Intra-candle SL/TP via high/low, SL assumed first when both could trigger.
  * Fixed fractional risk (2% of capital) with realistic fees + slippage.
  * Walk-forward 75/25 split to surface overfitting.
  * Last-90-day recency check to reject strategies that are dead today.
"""

import math
from . import signals

FEE_RATE = 0.0005       # 0.05% per side
SLIPPAGE = 0.0005       # 0.05%
STARTING_CAPITAL = 1000.0
RISK_PER_TRADE = 0.02   # 2% of capital per trade

_TF_MINUTES = {"m": 1, "h": 60, "d": 1440, "w": 10080}
_CANDLES_PER_DAY = {"15m": 96, "1h": 24, "4h": 6, "1d": 1}


def _timeframe_minutes(tf: str) -> int:
    if tf and tf[-1] in _TF_MINUTES:
        try:
            return int(tf[:-1]) * _TF_MINUTES[tf[-1]]
        except ValueError:
            pass
    return 60


def simulate(candles: list, strategy: dict) -> dict:
    """Run a single backtest pass and return performance stats."""
    sl_pct = strategy.get("stop_loss_pct", 2.0) / 100
    tp_pct = strategy.get("take_profit_pct", 4.0) / 100
    bias = strategy.get("directional_bias", "trend_following")

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    opens = [c.get("open", c["close"]) for c in candles]
    volumes = [c.get("volume", 0) for c in candles]

    sigs = signals.generate(bias, closes, highs, lows, volumes, opens)

    capital = STARTING_CAPITAL
    trades, monthly_pnl = [], {}
    in_trade = False
    trade_side = 0
    entry_price = 0.0
    risk_usdt = 0.0

    for i, candle in enumerate(candles):
        if capital <= 0:
            break

        if in_trade:
            high, low = candle["high"], candle["low"]
            position_size = risk_usdt / sl_pct  # fees scale with notional, not leverage

            if trade_side == 1:
                sl_hit = low <= entry_price * (1 - sl_pct)
                tp_hit = high >= entry_price * (1 + tp_pct)
                sl_exit = entry_price * (1 - sl_pct)
                tp_exit = entry_price * (1 + tp_pct)
            else:
                sl_hit = high >= entry_price * (1 + sl_pct)
                tp_hit = low <= entry_price * (1 - tp_pct)
                sl_exit = entry_price * (1 + sl_pct)
                tp_exit = entry_price * (1 - tp_pct)

            if sl_hit:  # conservative: SL first when both trigger
                pnl = -risk_usdt - 2 * position_size * FEE_RATE
                _record(trades, monthly_pnl, i, trade_side, entry_price, sl_exit, pnl, capital)
                capital = max(capital + pnl, 0.01)
                in_trade = False
            elif tp_hit:
                pnl = risk_usdt * (tp_pct / sl_pct) - 2 * position_size * FEE_RATE
                _record(trades, monthly_pnl, i, trade_side, entry_price, tp_exit, pnl, capital)
                capital += pnl
                in_trade = False

        if not in_trade and i > 0 and sigs[i - 1] != 0:
            sig = sigs[i - 1]
            in_trade = True
            trade_side = sig
            entry_price = candle["open"] * (1 + SLIPPAGE * sig)
            risk_usdt = capital * RISK_PER_TRADE

    return _stats(trades, monthly_pnl, capital)


def _record(trades, monthly_pnl, idx, side, entry_price, exit_price, pnl, capital_before):
    # Month bucketing uses trade index as a proxy timeline (relative, not absolute date).
    month_key = f"m{idx // 720:03d}"  # ~30d buckets at 1h candles; coarse but consistent
    monthly_pnl[month_key] = monthly_pnl.get(month_key, 0) + pnl
    trades.append({
        "side": "long" if side == 1 else "short",
        "entry_price": round(entry_price, 4),
        "exit_price": round(exit_price, 4),
        "pnl_usdt": round(pnl, 2),
        "capital_after": round(capital_before + pnl, 2),
    })


def _stats(trades, monthly_pnl, capital) -> dict:
    total = len(trades)
    if total == 0:
        return _empty_stats()

    winning = [t for t in trades if t["pnl_usdt"] > 0]
    losing = [t for t in trades if t["pnl_usdt"] <= 0]
    win_rate = len(winning) / total * 100

    avg_win = sum(t["pnl_usdt"] for t in winning) / max(len(winning), 1)
    avg_loss = abs(sum(t["pnl_usdt"] for t in losing) / max(len(losing), 1))
    profit_factor = 99.0 if not losing else (avg_win * len(winning)) / max(avg_loss * len(losing), 0.01)

    monthly_returns, running = {}, STARTING_CAPITAL
    for month in sorted(monthly_pnl.keys()):
        monthly_returns[month] = round(monthly_pnl[month] / max(running, 0.01) * 100, 2)
        running += monthly_pnl[month]
    monthly_vals = list(monthly_returns.values())
    avg_monthly = sum(monthly_vals) / len(monthly_vals) if monthly_vals else 0

    peak = running = STARTING_CAPITAL
    max_dd = 0.0
    for t in trades:
        running += t["pnl_usdt"]
        peak = max(peak, running)
        max_dd = max(max_dd, (peak - running) / peak * 100)

    RF_MONTHLY = 0.33
    if len(monthly_vals) > 1:
        variance = sum((r - avg_monthly) ** 2 for r in monthly_vals) / (len(monthly_vals) - 1)
        std = math.sqrt(variance)
        sharpe = (avg_monthly - RF_MONTHLY) / std * math.sqrt(12) if std > 0 else 0
    else:
        sharpe = 0

    max_consec_losing = consec = 0
    for v in monthly_vals:
        consec = consec + 1 if v < 0 else 0
        max_consec_losing = max(max_consec_losing, consec)

    return {
        "starting_capital": STARTING_CAPITAL,
        "final_balance": round(capital, 2),
        "total_trades": total,
        "win_rate": round(win_rate, 1),
        "avg_monthly_return": round(avg_monthly, 2),
        "max_drawdown": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "profit_factor": round(profit_factor, 2),
        "best_month": round(max(monthly_vals, default=0), 2),
        "worst_month": round(min(monthly_vals, default=0), 2),
        "max_consecutive_losing_months": max_consec_losing,
        "total_return_pct": round((capital - STARTING_CAPITAL) / STARTING_CAPITAL * 100, 2),
    }


def _empty_stats() -> dict:
    return {
        "starting_capital": STARTING_CAPITAL, "final_balance": STARTING_CAPITAL,
        "total_trades": 0, "win_rate": 0, "avg_monthly_return": 0,
        "max_drawdown": 0, "sharpe": 0, "profit_factor": 0,
        "best_month": 0, "worst_month": 0,
        "max_consecutive_losing_months": 0, "total_return_pct": 0,
    }


def walk_forward(candles: list, strategy: dict) -> dict:
    """75% in-sample / 25% out-of-sample split to detect overfitting."""
    if len(candles) < 400:
        return {"verdict": "insufficient_data", "consistency_score": 0.0,
                "in_sample_return": 0.0, "out_sample_return": 0.0}

    split = int(len(candles) * 0.75)
    is_stats = simulate(candles[:split], strategy)
    oos_stats = simulate(candles[split:], strategy)
    is_ret = is_stats.get("avg_monthly_return", 0)
    oos_ret = oos_stats.get("avg_monthly_return", 0)

    if is_ret > 0 and oos_ret > 0:
        ratio = min(oos_ret / is_ret, 2.0)
        verdict = "consistent" if ratio >= 0.3 else "degraded"
    elif is_ret > 0 and oos_ret > -1.0:
        ratio, verdict = 0.1, "degraded"
    elif is_ret > 0 and oos_ret <= -1.0:
        ratio, verdict = 0.0, "overfitting_suspected"
    else:
        ratio, verdict = 0.0, "insufficient_signal"

    return {
        "in_sample_return": round(is_ret, 2),
        "out_sample_return": round(oos_ret, 2),
        "consistency_score": round(min(max(ratio, 0.0), 2.0), 2),
        "verdict": verdict,
        "is_trades": is_stats.get("total_trades", 0),
        "oos_trades": oos_stats.get("total_trades", 0),
    }


def recency_check(candles: list, strategy: dict, days: int = 90) -> dict:
    """Backtest only the last `days` to confirm the edge is still alive today."""
    tf = strategy.get("timeframe", "4h")
    cpd = _CANDLES_PER_DAY.get(tf, 6)
    needed = days * cpd + 60  # +60 warmup candles for indicators
    if len(candles) <= needed:
        return {k: 0 for k in ("avg_monthly_return", "win_rate", "total_return_pct", "total_trades", "max_drawdown")}
    s = simulate(candles[-needed:], strategy)
    return {
        "avg_monthly_return": s["avg_monthly_return"],
        "win_rate": s["win_rate"],
        "total_return_pct": s["total_return_pct"],
        "total_trades": s["total_trades"],
        "max_drawdown": s["max_drawdown"],
    }


def full_backtest(candles: list, strategy: dict) -> dict:
    """Run the complete evaluation: full-period stats + walk-forward + recency."""
    if len(candles) < 50:
        return {**_empty_stats(), "candles_used": len(candles),
                "walk_forward": {}, "last_90d": {}}
    stats = simulate(candles, strategy)
    wf = walk_forward(candles, strategy) if len(candles) >= 200 else {}
    last_90d = recency_check(candles, strategy, 90)
    return {
        "strategy_name": strategy.get("strategy_name", "Strategy"),
        "token": strategy.get("token", strategy.get("pair", "?")),
        "timeframe": strategy.get("timeframe", "4h"),
        "candles_used": len(candles),
        **stats,
        "walk_forward": wf,
        "last_90d": last_90d,
    }
