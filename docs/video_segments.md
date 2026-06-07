# Demo Video — Segment-by-Segment Production Plan (AI voiceover)

Record each segment as a screen capture (Win + Alt + R), then overlay the English
AI voiceover. Voiceover is timed for ~150 words/min. Total ~85 seconds.

---

## Segment 0 — SETUP (do NOT record)

Open PowerShell, go to the project, and pre-run once so candle data is cached and
the recorded demo is fast:

```powershell
cd "C:\Users\Santoro\Documents\bnb-hack-cmc-skill"
python -m src.skill --token BTC
python -m src.skill --token ETH
```

Increase terminal font: Ctrl + mouse wheel up. Open the GitHub repo in a browser
tab: https://github.com/Gormathon12/cmc-quant-panel

---

## Segment 1 — Hook (~12s)

**Show:** the GitHub repo page (README visible).
**Voiceover (EN):**
> "Meet CMC Quant Panel. Most AI trading agents just ask a language model whether
> a token looks bullish. This one does something harder — it turns CoinMarketCap
> data into trading strategies you can actually backtest, and proves whether they work."

---

## Segment 2 — Run on Bitcoin (~26s)

**Run:**
```powershell
python -m src.skill --token BTC
```
**Show:** the report appearing. Slowly scroll so the sentiment line, the RANKING
table, and the WINNER block are all visible.
**Voiceover (EN):**
> "I give it a token — Bitcoin. It pulls live CoinMarketCap intelligence: the
> market regime, momentum, and the Fear and Greed index. Then a panel of AI agents
> generates five candidate strategies and backtests each one on two years of price
> data — no look-ahead bias, realistic fees, and a walk-forward test for
> overfitting. Here's the winner, with its full backtest and the panel's vote."

---

## Segment 3 — The wow: it rejects overfit strategies (~24s)

**Run:**
```powershell
python -m src.skill --token ETH
```
**Show:** the RANKING table. Hover/point the mouse at the rejected Volume Momentum
row (high Sharpe but REJECTED).
**Voiceover (EN):**
> "But the real magic is what it rejects. On Ethereum, this strategy shows a Sharpe
> ratio of two-point-five and nineteen percent a month. It looks incredible. The
> panel throws it out — because out of sample its edge collapses, and it's been
> losing money for ninety days. It's overfit. A naive agent would recommend it.
> This one won't."

---

## Segment 4 — Rigor (~12s)

**Run:**
```powershell
python -m pytest -q
```
**Show:** the green dots / "17 passed".
**Voiceover (EN):**
> "And it's built to be trusted — seventeen unit tests, including an explicit
> no-look-ahead contract for the backtester."

---

## Segment 5 — It's a real Skill + close (~12s)

**Show:** back to the GitHub repo — scroll to the architecture diagram and the
"Use it as a Skill (MCP server)" section.
**Voiceover (EN):**
> "It's also a Model Context Protocol server, so any agent can call it as a Skill.
> Open source, backtested, powered by CoinMarketCap. That's CMC Quant Panel —
> built for BNB Hack, Track Two."

---

## After recording
- Stitch the segments (any editor: CapCut, Clipchamp on Windows, DaVinci Resolve).
- Drop the AI voiceover over each segment; trim silences.
- Add the captions if you want belt-and-suspenders.
- Upload to YouTube as **Unlisted**, paste the link in the BUIDL submission.
