"""
Smoke test: fetch real OHLCV and run the full backtest across all signal families.
No API key required (uses the Binance public OHLCV provider).

Run from project root:  python -m tests.smoke
"""

from src.data.ohlcv import fetch_ohlcv
from src.engine import backtester, indicators, signals


def main():
    token = "BTC"
    timeframe = "4h"
    print(f"Fetching {token} {timeframe} OHLCV (730d)...")
    candles = fetch_ohlcv(token, timeframe, days=730)
    print(f"  -> {len(candles)} candles")
    assert len(candles) > 500, "expected plenty of candles"

    snap = indicators.snapshot(candles)
    print(f"Snapshot: price={snap['price']} rsi={snap['rsi_14']} "
          f"atr%={snap['atr_pct']} trend={snap['trend']}")

    print("\nBacktesting every signal family on BTC 4h:")
    print(f"{'bias':<20}{'trades':>7}{'win%':>7}{'avg/mo%':>9}{'maxDD%':>8}{'sharpe':>8}{'WF':>16}")
    biases = [
        "trend_following", "mean_reversion", "breakout", "long_only", "short_only",
        "volume_momentum", "macd_momentum", "scalper", "rsi_divergence",
        "bollinger_squeeze", "stoch_rsi", "supertrend", "ema_cross_1h", "heikin_ashi",
    ]
    for bias in biases:
        strat = {"strategy_name": bias, "token": token, "timeframe": timeframe,
                 "directional_bias": bias, "stop_loss_pct": 2.0, "take_profit_pct": 5.0}
        r = backtester.full_backtest(candles, strat)
        wf = r.get("walk_forward", {}).get("verdict", "-")
        print(f"{bias:<20}{r['total_trades']:>7}{r['win_rate']:>7}"
              f"{r['avg_monthly_return']:>9}{r['max_drawdown']:>8}{r['sharpe']:>8}{wf:>16}")

    print("\nSmoke test passed.")


if __name__ == "__main__":
    main()
