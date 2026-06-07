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
  skill.py     CLI entry point: run_skill(token) -> spec + report + verdict
  mcp_server.py  MCP server exposing the pipeline as a routable Skill
examples/      Sample outputs + MCP client config
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
python -m src.skill --token ETH --timeframe 4h --json examples/eth_report.json
```

## Example output

Running the Skill on BTC produces a backtested strategy spec, a ranking, and a
transparent panel verdict (full file: [examples/btc_report.txt](examples/btc_report.txt)):

```
  CMC QUANT PANEL — second opinion for BTC
======================================================================
Regime: trending   |   BTC ... RSI 41.3, ATR 1.98%, trend strong_downtrend.
Sentiment: Fear&Greed 15/100 (Extreme fear)  7d -14.6%  30d -21.5%

Candidates evaluated: 5  (audit-approved: 2)

RANKING
  strategy                    score  avg/mo%  sharpe      audit   panel
  Volume Momentum BTC 4h     23.404     8.04    1.37   APPROVED   MIXED
  EMA Trend BTC 4h            9.656     1.42     0.3   APPROVED    SKIP
  Heikin Ashi Trend BTC 4h   -998.4    11.23     1.6   REJECTED    SKIP   <- 11%/mo but REJECTED
  MACD Momentum BTC 4h      -999.04     6.88    0.96   REJECTED    SKIP
  Bear Momentum BTC 4h      -1002.5     -6.9   -2.54   REJECTED    SKIP

  WINNER: Volume Momentum BTC 4h
  Backtest (4380 candles): 8.04%/mo, WR 29.7%, maxDD 36.07%, Sharpe 1.37, 212 trades
  Walk-forward: consistent (IS 1.44%/mo, OOS 24.65%/mo)
  Last 90d: 35.48%/mo, WR 47.4%, 19 trades
  Panel: split vote (DEPLOY 0 / NEEDS_WORK 8 / SKIP 0)
```

**The headline isn't the winner — it's the rejections.** On ETH, a Volume Momentum
strategy shows Sharpe **2.53** and **+19%/mo**, yet the panel *rejects* it: walk-forward
collapses from +26.8%/mo in-sample to **−2.4%/mo** out-of-sample, and it has lost
**−17.5%/mo over the last 90 days**. A naive "is this bullish?" agent would have
recommended it. This one throws it out. That discipline is the whole point.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The suite (`tests/test_engine.py`) covers indicator alignment, the signal value
domain, the **no-look-ahead** entry contract, backtest determinism, and stat
sanity — all on synthetic data, no network needed.

## Use it as a Skill (MCP server)

Beyond the CLI, the whole pipeline is exposed as an **MCP server**, so any
MCP-compatible agent (Claude, Cursor, the CMC Agent Hub) can route a query to it
and get a decision-ready result instead of raw data — which is exactly what a
"Skill" is in the CMC marketplace sense.

```bash
python -m pip install -r requirements-mcp.txt
python -m src.mcp_server          # stdio MCP server
```

Tools exposed:

| Tool | What it does |
|------|--------------|
| `analyze_token(token, timeframe)` | Full pipeline → backtested, panel-reviewed strategy recommendation |
| `token_intelligence(token)` | Fast CMC read: quote, momentum, fundamentals, global regime, Fear & Greed |

Wire it into a client with [examples/mcp_config.json](examples/mcp_config.json).

Data can come from CoinMarketCap two ways: the **Pro REST API** (used here, set
`cmc_api_key` in `config.json`) or the official **CMC Data MCP**
(`https://mcp.coinmarketcap.com/mcp`, `X-CMC-MCP-API-KEY` header) — same data,
your choice of transport.

## Status

- [x] Project scaffold (independent — no dependency on any other project)
- [x] OHLCV provider (Binance public — works without any key)
- [x] Quant engine ported + verified on real data: indicators, 13 signal generators, backtester, walk-forward, recency check
- [x] CMC client (intelligence layer): quotes, momentum, fundamentals, global regime, Fear & Greed
- [x] Multi-agent panel (scout, architects, risk, devil's advocate, voting, arbitrator)
- [x] Skill entry point + report formatting (`python -m src.skill --token BTC`)
- [x] Sample outputs (examples/)
- [x] Unit tests for the engine (17 tests, incl. no-look-ahead contract)
- [x] `supertrend` generator fixed (proper trailing-band flips)
- [x] Exposed as an MCP server (routable Skill: `analyze_token`, `token_intelligence`)
- [ ] Demo video

> Working MVP: the full pipeline runs end-to-end and correctly rejects overfit /
> recently-losing strategies (verified on BTC, ETH, BNB).

## License

**PolyForm Noncommercial 1.0.0** — see [LICENSE](LICENSE). The source is open for
review, learning, and noncommercial use, but commercial use (including paid
products or services built on it) requires a separate license from the author.
Independent project built for BNB Hack 2026.

Copyright (c) 2026 Facundo Santoro (Gormathon / Alpha Signals).
