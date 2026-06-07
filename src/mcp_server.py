"""
MCP server — exposes the CMC Quant Panel as a routable Skill.

This turns the whole pipeline into a tool any MCP-compatible agent (Claude,
Cursor, the CMC Agent Hub, ...) can call: hand it a token, get back a
decision-ready strategy recommendation with a backtested, panel-reviewed verdict
— not raw data. That is exactly what a "Skill" is in the CMC marketplace sense.

Run as an MCP server (stdio transport):
    python -m src.mcp_server

Client config (e.g. Claude Desktop / Cursor mcpServers):
    {
      "mcpServers": {
        "cmc-quant-panel": {
          "command": "python",
          "args": ["-m", "src.mcp_server"],
          "cwd": "C:/path/to/cmc-quant-panel"
        }
      }
    }
"""

from mcp.server.fastmcp import FastMCP

from .skill import run_skill, agent_summary
from .cmc import client as cmc

mcp = FastMCP("CMC Quant Panel")


@mcp.tool()
def analyze_token(token: str, timeframe: str = "4h") -> dict:
    """
    Generate a backtested, panel-reviewed trading strategy recommendation for a
    crypto token using CoinMarketCap data.

    Returns a decision-ready summary: market regime, sentiment, the recommended
    strategy with its backtest (return, Sharpe, drawdown, walk-forward, last-90d),
    the panel verdict, and which candidate strategies were rejected and why.

    Args:
        token: Token symbol, e.g. "BTC", "ETH", "BNB", "SOL".
        timeframe: Candle timeframe for the backtest ("15m", "1h", "4h", "1d").
    """
    result = run_skill(token, timeframe)
    return agent_summary(result)


@mcp.tool()
def token_intelligence(token: str) -> dict:
    """
    Fetch raw CoinMarketCap intelligence for a token without running the full
    strategy pipeline: latest quote + momentum, fundamentals, global market
    regime, and the Fear & Greed index. Fast; good for a quick read.

    Args:
        token: Token symbol, e.g. "BTC", "ETH", "BNB".
    """
    return cmc.intelligence(token)


if __name__ == "__main__":
    mcp.run()
