# BUIDL Submission — CMC Quant Panel

**Track:** Track 2 — Strategy Skills (Crypto Intelligence Agent)
**Repo:** https://github.com/Gormathon12/cmc-quant-panel

---

## Tagline

An AI multi-agent Skill that turns CoinMarketCap data into **backtestable trading
strategies** — and rejects the ones that only look good on paper.

---

## The problem

Most "AI trading" tools do one thing: fetch some data and ask an LLM "is this
token bullish?". That produces confident-sounding answers with zero proof. Anyone
can generate a strategy that looks amazing on a backtest by accident — the hard
part is knowing whether an edge is *real* or just overfit to the past.

## What CMC Quant Panel does

You give it a token. It returns a **backtestable strategy spec**, a full backtest
report, and a transparent verdict from a panel of specialist AI agents:

1. **Market Scout** fuses CoinMarketCap intelligence (price momentum, fundamentals,
   global regime, Fear & Greed) with a technical snapshot to classify the market
   regime and pick which strategy families fit.
2. **Strategy Architects** generate candidate strategies across 13 signal families
   (trend, breakout, mean-reversion, RSI divergence, Bollinger squeeze, SuperTrend,
   MACD, and more), with stops scaled to current volatility.
3. **Backtester** runs each candidate on real historical OHLCV with **no
   look-ahead bias**, realistic fees + slippage, fixed fractional risk, a **75/25
   walk-forward split** (overfitting detection), and a **last-90-day recency check**.
4. **Risk Assessor / Auditor** size leverage and apply hard pass/fail criteria.
5. **Devil's Advocate** argues against each strategy and assigns a risk flag.
6. **Voting Panel** — 8 specialist personas cast transparent DEPLOY / SKIP /
   NEEDS_WORK votes with justifications.
7. **Arbitrator** ranks everything and picks the winner.

## What makes it different — the rejections

The headline isn't the strategy it recommends; it's the ones it **throws out**.

> On ETH, a Volume Momentum strategy shows Sharpe **2.53** and **+19%/mo**. The
> panel **rejects** it: walk-forward collapses from +26.8%/mo in-sample to
> **−2.4%/mo** out-of-sample, and it has lost **−17.5%/mo over the last 90 days**.

A naive agent recommends it. This one proves it's overfit and dead, and discards
it. That discipline — proof over vibes — is the entire value proposition.

## Powered by CoinMarketCap

The intelligence layer is CMC: latest quotes + multi-horizon momentum, project
fundamentals/metadata, global market regime (BTC dominance, total-cap trend), and
the Fear & Greed index. Works via the CMC Pro REST API, and is documented to run
against the official CMC Data MCP (`mcp.coinmarketcap.com/mcp`) — same data, your
choice of transport.

## It's a real Skill (MCP)

Beyond a CLI, the whole pipeline is exposed as an **MCP server**, so any agent
(Claude, Cursor, the CMC Agent Hub) can route a query to it and get a
decision-ready recommendation instead of raw data — exactly what a "Skill" is in
the CMC marketplace sense. Tools: `analyze_token(token, timeframe)` and
`token_intelligence(token)`.

## Rigor

- 17 unit tests, including an explicit **no-look-ahead entry contract** test.
- Deterministic, reproducible backtests on synthetic and live data.
- No live execution, no custody, no real funds — a pure quant research Skill, as
  Track 2 asks.

## Tech

Python (stdlib + `requests`), official `mcp` SDK for the server, CoinMarketCap Pro
API, Binance public REST for backtest OHLCV (pluggable). No heavyweight ML deps —
the edge is in the methodology, not a black box.

## Try it

```bash
pip install -r requirements.txt
cp config.example.json config.json      # add your CMC API key
python -m src.skill --token BTC
python -m pytest -q
```

## License

PolyForm Noncommercial 1.0.0 — open for review and noncommercial use; commercial
use requires a separate license.
