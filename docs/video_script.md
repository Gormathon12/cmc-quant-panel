# Demo Video Script — CMC Quant Panel (~90 seconds)

Goal: prove, on screen, that this generates *backtestable* strategies and rejects
overfit ones. Screen recording only (Win + Alt + R to start/stop on Windows 10).
Recording lands in `Videos/Captures`.

Narration is optional — the on-screen captions tell the whole story, so you can
record with no voice and just let the captions + terminal do the talking.

Before recording: open a terminal in the project folder, make the font large
(Ctrl + Mouse wheel up), and have the GitHub repo open in a browser tab.

---

## Scene 1 — Hook (0:00–0:10)

**On screen:** title card or just the terminal with this caption overlaid.
**Caption:** "CMC Quant Panel — turns CoinMarketCap data into backtestable trading strategies."
**Optional voiceover:** "Most AI trading tools just ask an LLM if a token is bullish. This one proves it."

## Scene 2 — Run it on BTC (0:10–0:45)

**Do:** type and run
```
python -m src.skill --token BTC
```
**As the report appears, caption the key parts:**
- "Live CoinMarketCap data: regime + Fear & Greed" (point at the sentiment line)
- "5 strategies generated, backtested on 2 years of data"
- "Winner: backtested, walk-forward validated, panel-reviewed"

**Optional voiceover:** "It pulls CMC intelligence, generates candidate strategies, backtests each one with no look-ahead bias, and a panel of agents votes on them."

## Scene 3 — The wow: it rejects overfit strategies (0:45–1:05)

**Do:** run
```
python -m src.skill --token ETH
```
**Caption (the money shot):** "This strategy shows Sharpe 2.53 and +19%/mo — and the panel REJECTS it."
**Then caption:** "Why? Walk-forward collapses out-of-sample, and it's lost money for 90 days. Overfit. Discarded."

**Optional voiceover:** "Anyone can find a strategy that looks great by accident. The point is throwing those out. Proof over vibes."

## Scene 4 — Rigor (1:05–1:20)

**Do:** run
```
python -m pytest -q
```
**Caption:** "17 tests green — including a no-look-ahead backtest contract."

## Scene 5 — It's a real Skill + close (1:20–1:30)

**Do:** switch to the browser, show the GitHub repo (README with the diagram).
**Caption:** "Also an MCP server — any agent can call it as a Skill. Powered by CoinMarketCap. BNB Hack Track 2."
**Optional voiceover:** "Open source, backtested, agent-ready. That's CMC Quant Panel."

---

## Tips
- Keep it under 2 minutes. Judges watch a lot of these.
- If a command is slow the first time (downloading candles), run it once before
  recording so the data is cached and the demo is snappy.
- Free tools if you prefer: OBS Studio (more control) or Loom (records screen +
  voice from the browser, easiest for narration).
- Upload to YouTube as "unlisted" and paste the link in the BUIDL submission.
