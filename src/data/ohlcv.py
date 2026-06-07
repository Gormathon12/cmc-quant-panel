"""
Pluggable OHLCV provider for backtesting.

The Skill's *intelligence* comes from CoinMarketCap (quotes, technicals, sentiment),
but historical candle data for backtesting is fetched from a pluggable source so the
backtest can always run. Default provider is Binance's public REST API (no key
required); a CMC OHLCV provider can be swapped in via config when the API tier allows.

Returns candles as list of dicts: [{open, high, low, close, volume}, ...]
"""

import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data_cache"
DEFAULT_CACHE_HOURS = 12


def _cache_path(symbol: str, timeframe: str, days: int) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = symbol.replace("/", "")
    return CACHE_DIR / f"{safe}_{timeframe}_{days}d.json"


def _cache_valid(path: Path, max_age_hours: int = DEFAULT_CACHE_HOURS) -> bool:
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < max_age_hours


def to_symbol(token: str, quote: str = "USDT") -> str:
    """Normalize a token ('BTC', 'btc', 'BTC/USDT', 'BTCUSDT') to a trading symbol."""
    t = token.upper().replace("/", "")
    for q in ("USDT", "BUSD", "USDC"):
        if t.endswith(q):
            return t
    return t + quote


def fetch_ohlcv(token: str, timeframe: str = "1h", days: int = 730,
                provider: str = "binance") -> list:
    """Fetch historical OHLCV for a token. Cached for 12h. Provider is pluggable."""
    if provider == "binance":
        return _fetch_binance(token, timeframe, days)
    raise ValueError(f"Unknown OHLCV provider: {provider}")


def _fetch_binance(token: str, timeframe: str, days: int) -> list:
    """Fetch real OHLCV from Binance public REST API (no auth)."""
    import requests

    symbol = to_symbol(token)
    cache = _cache_path(symbol, timeframe, days)
    if _cache_valid(cache):
        with open(cache) as f:
            return json.load(f)

    since = int((time.time() - days * 86400) * 1000)
    all_bars = []
    delay = 0.5

    while True:
        try:
            r = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": symbol, "interval": timeframe,
                        "startTime": since, "limit": 1000},
                timeout=15,
            )
            bars = r.json()
            if not isinstance(bars, list):
                print(f"[ohlcv] Unexpected response for {symbol}: {bars}")
                break
        except Exception as e:
            print(f"[ohlcv] Error fetching {symbol} {timeframe}: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay = min(delay * 2, 30)
            continue

        if not bars:
            break

        all_bars.extend(bars)
        last_ts = bars[-1][0]
        if last_ts >= int(time.time() * 1000) - 60_000 or len(bars) < 1000:
            break

        since = last_ts + 1
        delay = 0.5
        time.sleep(0.25)  # courtesy rate limit

    candles = [
        {"open": float(b[1]), "high": float(b[2]), "low": float(b[3]),
         "close": float(b[4]), "volume": float(b[5])}
        for b in all_bars
    ]

    if candles:
        with open(cache, "w") as f:
            json.dump(candles, f)

    return candles
