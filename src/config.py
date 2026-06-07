"""Config loader — reads config.json from the project root (gitignored)."""

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _ROOT / "config.json"
_EXAMPLE_PATH = _ROOT / "config.example.json"

_cache = None


def load() -> dict:
    """Load config.json, falling back to config.example.json. Cached."""
    global _cache
    if _cache is not None:
        return _cache
    path = _CONFIG_PATH if _CONFIG_PATH.exists() else _EXAMPLE_PATH
    with open(path) as f:
        _cache = json.load(f)
    return _cache


def cmc_api_key() -> str:
    key = load().get("cmc_api_key", "")
    if not key or key.startswith("YOUR_"):
        raise ValueError(
            "No CoinMarketCap API key configured. Copy config.example.json to "
            "config.json and set 'cmc_api_key'. Get a free key at "
            "https://coinmarketcap.com/api/"
        )
    return key
