"""
Lorcast MCP Server — Disney Lorcana Card Data
===============================================
A Model Context Protocol (MCP) server that exposes the Lorcast REST API
endpoints as MCP tools, providing programmatic access to Disney Lorcana
Trading Card Game data including sets, cards, search and card images.

Base URL : https://api.lorcast.com/v0
API Docs : https://lorcast.com/docs/api

Authentication
--------------
The Lorcast API is **public** and does not require authentication.
Please respect the rate limit of ~10 requests/second (50-100 ms between
requests).
"""

import os
import re
import json
import time
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional, List
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def _parse_changelog(changelog: str) -> List[Dict[str, Any]]:
    pattern = re.compile(
        r"^##+\s*\[?v?(\d+\.\d+\.\d+(?:-[^\]\s]+)?)\]?\s*-?\s*"
        r"([0-9]{4}-[0-9]{2}-[0-9]{2})?\s*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(changelog))
    entries: List[Dict[str, Any]] = []
    for i, m in enumerate(matches):
        v, date = m.group(1), m.group(2)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(changelog)
        section = changelog[start:end].strip()
        changes: Dict[str, List[str]] = {}
        tp = re.compile(r"^###\s+([A-Za-z ]+)\s*$", re.MULTILINE)
        tms = list(tp.finditer(section))
        for j, t in enumerate(tms):
            ct = t.group(1).strip()
            ts = t.end()
            te = tms[j + 1].start() if j + 1 < len(tms) else len(section)
            bullets = re.findall(r"^[-*]\s+(.*)$", section[ts:te], re.MULTILINE)
            changes[ct] = bullets
        entries.append({"version": v, "date": date, "changes": changes})
    return entries


# ---------------------------------------------------------------------------
# HTTP Client
# ---------------------------------------------------------------------------

BASE_URL = "https://api.lorcast.com/v0"

# Simple rate-limit helper: track last request time
_last_request_time: float = 0.0
_MIN_INTERVAL: float = 0.1  # 100 ms between requests


def _throttle() -> None:
    """Ensure at least _MIN_INTERVAL seconds between API calls."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Perform a GET request against the Lorcast API."""
    _throttle()
    r = requests.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        params=params,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def _ok(data: Any) -> str:
    return json.dumps(data, indent=2)


def _err(msg: Any) -> str:
    return json.dumps({"error": str(msg)})


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

_DIR = os.path.dirname(__file__)

mcp = FastMCP("Lorcast – Disney Lorcana Card Data")


# ---- Version / Info -------------------------------------------------------

@mcp.tool()
def show_version() -> str:
    """Show the Lorcast MCP server version, changelog, and API information."""
    try:
        version = _read_file(os.path.join(_DIR, "VERSION")).strip()
        changelog_raw = _read_file(os.path.join(_DIR, "CHANGELOG.md"))
        entries = _parse_changelog(changelog_raw)
        return _ok({
            "server": "Lorcast MCP Server",
            "version": version,
            "api_base_url": BASE_URL,
            "api_docs": "https://lorcast.com/docs/api",
            "changelog": entries[:5],
        })
    except Exception as e:
        return _err(e)


# ---- Sets -----------------------------------------------------------------

@mcp.tool()
def list_sets() -> str:
    """List all Disney Lorcana card sets (standard and promotional).

    Returns a list of sets with id, name, code, released_at, and
    prereleased_at fields.
    """
    try:
        data = _get("sets")
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_set(set_id: str) -> str:
    """Get detailed information about a specific Lorcana set.

    Args:
        set_id: The set code (e.g. "1", "D100") or the full set ID
                (e.g. "set_7ecb0e0c71af496a9e0110e23824e0a5").
    """
    try:
        data = _get(f"sets/{set_id}")
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_set_cards(set_id: str) -> str:
    """Get all cards belonging to a specific Lorcana set.

    Returns the full card objects for every card in the set.

    Args:
        set_id: The set code (e.g. "1") or the full set ID.
    """
    try:
        data = _get(f"sets/{set_id}/cards")
        return _ok(data)
    except Exception as e:
        return _err(e)


# ---- Cards ----------------------------------------------------------------

@mcp.tool()
def search_cards(q: str, unique: Optional[str] = None) -> str:
    """Search the Lorcana card database using full-text search.

    Supports the Lorcast search syntax for filtering by attributes such as
    set, rarity, ink color, cost, type, etc.

    Examples:
      - "elsa" — find all cards named Elsa
      - "elsa set:1 rarity:enchanted" — Elsa from The First Chapter, Enchanted
      - "ink:amethyst cost:3" — Amethyst cards costing 3

    See https://lorcast.com/docs/syntax for the full syntax guide.

    Args:
        q: The search query string (will be URL-encoded automatically).
        unique: Optional deduplication mode:
                "cards" (default) — removes duplicate gameplay objects.
                "prints" — returns all prints for matched cards.
    """
    try:
        params: Dict[str, Any] = {"q": q}
        if unique:
            params["unique"] = unique
        data = _get("cards/search", params=params)
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_card(set_code: str, collector_number: str) -> str:
    """Get a specific Lorcana card by its set and collector number.

    Args:
        set_code: The set code or identifier (e.g. "1").
        collector_number: The card's collector number within the set (e.g. "207").
    """
    try:
        data = _get(f"cards/{set_code}/{collector_number}")
        return _ok(data)
    except Exception as e:
        return _err(e)


# ---- Card Images ----------------------------------------------------------

@mcp.tool()
def get_card_image_uris(set_code: str, collector_number: str) -> str:
    """Get image URLs for a specific Lorcana card.

    Returns URLs for small (146×204), normal (488×681), and large (674×940)
    digital card images in AVIF format, served from the Lorcast CDN.

    Args:
        set_code: The set code or identifier (e.g. "1").
        collector_number: The card's collector number within the set (e.g. "207").
    """
    try:
        card = _get(f"cards/{set_code}/{collector_number}")
        image_uris = card.get("image_uris", {})
        return _ok({
            "card_id": card.get("id"),
            "name": card.get("name"),
            "version": card.get("version"),
            "image_uris": image_uris,
        })
    except Exception as e:
        return _err(e)


# ---- Convenience / Composite Tools ----------------------------------------

@mcp.tool()
def get_card_prices(set_code: str, collector_number: str) -> str:
    """Get pricing information for a specific Lorcana card.

    Returns USD prices for normal and foil versions. Prices are updated
    once per day.

    Args:
        set_code: The set code or identifier (e.g. "1").
        collector_number: The card's collector number within the set (e.g. "207").
    """
    try:
        card = _get(f"cards/{set_code}/{collector_number}")
        return _ok({
            "card_id": card.get("id"),
            "name": card.get("name"),
            "version": card.get("version"),
            "set": card.get("set"),
            "rarity": card.get("rarity"),
            "collector_number": card.get("collector_number"),
            "prices": card.get("prices", {}),
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_cards_by_ink(ink: str) -> str:
    """Search for Lorcana cards by ink color.

    Args:
        ink: The ink color to filter by. One of: Amber, Amethyst, Emerald,
             Ruby, Sapphire, Steel.
    """
    try:
        data = _get("cards/search", params={"q": f"ink:{ink}"})
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_cards_by_rarity(rarity: str) -> str:
    """Search for Lorcana cards by rarity.

    Args:
        rarity: The rarity level. One of: Common, Uncommon, Rare,
                Super_rare, Legendary, Enchanted, Promo.
    """
    try:
        data = _get("cards/search", params={"q": f"rarity:{rarity}"})
        return _ok(data)
    except Exception as e:
        return _err(e)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
