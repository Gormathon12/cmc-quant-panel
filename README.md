# CMC Quant Panel — Backtestable Strategy Skill

**BNB Hack: AI Trading Agent Edition · Track 2 (Strategy Skills) · Powered by CoinMarketCap**

A **CMC Skill** that turns CoinMarketCap market data into **backtestable trading
strategies**, validated by a multi-agent review panel and a rigorous historical
backtest (walk-forward + recency tested). You give it a token; it gives you a
strategy spec, a backtest report, and a panel verdict — a "second opinion" you
can trust because it's proven on history, not vibes.

> Track 2 asks for a *backtestable spec, not a live agent*. This is exactly that:
> no live execution, no real funds, no wallet signing. Pure quant research.

---

## Why this wins

Most submissions will fetch CMC data and ask an LLM "is this token bullish?".
This does more:

1. **Generates** candidate strategies across 13 signal families (trend, breakout,
   mean-reversion, RSI divergence, Bollinger squeeze, SuperTrend, MACD, and more).
2. **Backtests** every candidate on real historical OHLCV — with no look-ahead bias,
   realistic fees + slippage, and fixed risk-per-trade sizing.
3. **Validates** against overfitting via 75/25 walk-forward split and a last-90-day
   recency check (a strategy that backtested well years ago but is dead today is
   rejected).
4. **Reviews** via a panel of specialist agents (scout, architects, risk assessor,
   risk auditor, devil's advocate) that **vote** — a transparent second opinion.
5. **Outputs** a clean, backtestable strategy spec (JSON) + a human-readable report.

The backtester is the moat: a strategy spec is only worth something if you can
prove it works.

---

## Architecture

```
token in
   │
   ▼
┌──────────────┐   CMC data (quotes, technicals, sentiment, regime)
│ Market Scout │◄──────────────────────────────────────────────────┐
└──────┬───────┘                                                    │
       ▼                                                     ┌───────┴───────┐
┌──────────────┐   candidate strategies                     │  CMC client   │
│  Architects  │──────────────┐                             │ (CoinMarketCap)│
└──────────────┘              ▼                             └───────────────┘
                       ┌──────────────┐   historical OHLCV
                       │  Backtester  │◄──────────── OHLCV provider (pluggable)
                       └──────┬───────┘
                              ▼
              ┌────────────────────────────────┐
              │ Risk · Devil's Advocate · Panel │  → vote: DEPLOY / SKIP / NEEDS_WORK
              └────────────────┬───────────────┘
                               ▼
                    strategy spec + backtest report + verdict
```

## Project layout

```
src/
  data/        OHLCV provider (pluggable: Binance public now, CMC OHLCV when available)
  cmc/         CoinMarketCap client — the intelligence layer (quotes, sentiment, technicals)
  engine/      Deterministic quant core: indicators, signal generators, backtester, templates
  panel/       Multi-agent review: scout, architects, risk, devil's advocate, voting, arbitrator
  skill.py     Entry point: run_skill(token) -> spec + report + verdict
examples/      Sample outputs
tests/         Unit tests for the engine
```

## Setup

```bash
pip install -r requirements.txt
cp config.example.json config.json   # then add your CMC API key
```

Get a free CoinMarketCap API key (Basic tier, 15k credits/month):
https://coinmarketcap.com/api/

## Usage

```bash
python -m src.skill --token BTC
```

## Status

- [x] Project scaffold (independent — no dependency on any other project)
- [x] OHLCV provider (Binance public — works without any key)
- [x] Quant engine ported + verified on real data: indicators, 13 signal generators, backtester, walk-forward, recency check
- [x] CMC client (intelligence layer): quotes, momentum, fundamentals, global regime, Fear & Greed
- [x] Multi-agent panel (scout, architects, risk, devil's advocate, voting, arbitrator)
- [x] Skill entry point + report formatting (`python -m src.skill --token BTC`)
- [x] Sample outputs (examples/)
- [ ] Unit tests for the engine
- [ ] Package as a CMC Skill (skills-marketplace format) + demo video
- [ ] Polish: fix `supertrend` band switch (currently 0 trades)

> Working MVP: the full pipeline runs end-to-end and correctly rejects overfit /
> recently-losing strategies (verified on BTC, ETH, BNB).

## License

**PolyForm Noncommercial 1.0.0** — see [LICENSE](LICENSE). The source is open for
review, learning, and noncommercial use, but commercial use (including paid
products or services built on it) requires a separate license from the author.
Independent project built for BNB Hack 2026.

Copyright (c) 2026 Facundo Santoro (Gormathon / Alpha Signals).
