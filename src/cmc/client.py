"""
CoinMarketCap Pro API client — the intelligence layer.

Pulls decision-ready signals the backtester can't see from price alone:
latest quote + momentum, project fundamentals/metadata, global market regime
(BTC dominance, total cap trend), and the Fear & Greed index.

All calls are cached briefly to stay well within the free Basic tier (15k
credits/month). Network/tier failures degrade gracefully to None so the Skill
still runs on price data alone.
"""

import time

from .. import config

BASE = "https://pro-api.coinmarketcap.com"
_CACHE_TTL = 300  # seconds
_cache: dict = {}


def _get(endpoint: str, params: dict = None) -> dict:
    """GET a CMC endpoint with short-lived caching. Raises on HTTP/network error."""
    import requests

    key = (endpoint, tuple(sorted((params or {}).items())))
    hit = _cache.get(key)
    if hit and (time.time() - hit[0]) < _CACHE_TTL:
        return hit[1]

    r = requests.get(
        BASE + endpoint,
        headers={"X-CMC_PRO_API_KEY": config.cmc_api_key(), "Accept": "application/json"},
        params=params or {},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    status = data.get("status", {})
    # error_code comes back as int 0 on some endpoints and string "0" on others.
    code = status.get("error_code")
    if code not in (None, 0, "0"):
        raise RuntimeError(f"CMC error {code}: {status.get('error_message')}")

    _cache[key] = (time.time(), data)
    return data


def quote(symbol: str) -> dict:
    """Latest price + multi-horizon momentum + market cap for a token."""
    data = _get("/v2/cryptocurrency/quotes/latest", {"symbol": symbol.upper()})
    arr = data.get("data", {}).get(symbol.upper(), [])
    if not arr:
        return {}
    c = arr[0]
    q = c.get("quote", {}).get("USD", {})
    return {
        "symbol": c.get("symbol"),
        "name": c.get("name"),
        "price": q.get("price"),
        "percent_change_1h": q.get("percent_change_1h"),
        "percent_change_24h": q.get("percent_change_24h"),
        "percent_change_7d": q.get("percent_change_7d"),
        "percent_change_30d": q.get("percent_change_30d"),
        "volume_24h": q.get("volume_24h"),
        "volume_change_24h": q.get("volume_change_24h"),
        "market_cap": q.get("market_cap"),
        "market_cap_dominance": q.get("market_cap_dominance"),
        "cmc_rank": c.get("cmc_rank"),
        "circulating_supply": c.get("circulating_supply"),
        "max_supply": c.get("max_supply"),
    }


def fundamentals(symbol: str) -> dict:
    """Project metadata: category, tags, description, launch date, links."""
    data = _get("/v2/cryptocurrency/info", {"symbol": symbol.upper()})
    arr = data.get("data", {}).get(symbol.upper(), [])
    if not arr:
        return {}
    c = arr[0]
    return {
        "category": c.get("category"),
        "tags": (c.get("tags") or [])[:12],
        "description": c.get("description"),
        "date_added": c.get("date_added"),
        "website": (c.get("urls", {}).get("website") or [None])[0],
    }


def global_metrics() -> dict:
    """Market-wide regime: BTC dominance, total cap and its 24h move."""
    data = _get("/v1/global-metrics/quotes/latest")
    d = data.get("data", {})
    q = d.get("quote", {}).get("USD", {})
    return {
        "btc_dominance": d.get("btc_dominance"),
        "eth_dominance": d.get("eth_dominance"),
        "total_market_cap": q.get("total_market_cap"),
        "total_market_cap_change_24h": q.get("total_market_cap_yesterday_percentage_change"),
        "total_volume_24h": q.get("total_volume_24h"),
    }


def fear_greed() -> dict:
    """CMC Fear & Greed index (0-100) with its classification."""
    try:
        data = _get("/v3/fear-and-greed/latest")
        d = data.get("data", {})
        return {"value": d.get("value"), "classification": d.get("value_classification")}
    except Exception:
        return {"value": None, "classification": None}


def intelligence(symbol: str) -> dict:
    """One-shot bundle of all CMC intelligence for a token. Degrades gracefully."""
    out = {"symbol": symbol.upper()}
    for name, fn in (("quote", lambda: quote(symbol)),
                     ("fundamentals", lambda: fundamentals(symbol)),
                     ("global", global_metrics),
                     ("fear_greed", fear_greed)):
        try:
            out[name] = fn()
        except Exception as e:
            print(f"[cmc] {name} unavailable: {e}")
            out[name] = {}
    return out
