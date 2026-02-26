# Lorcast MCP Server — Disney Lorcana Card Data

A Model Context Protocol (MCP) server that provides read-only access to Disney Lorcana Trading Card Game data via the [Lorcast API](https://lorcast.com/docs/api). Browse sets, search cards, retrieve card details, images, and pricing information.

**API Base URL:** `https://api.lorcast.com/v0`
**API Docs:** [https://lorcast.com/docs/api](https://lorcast.com/docs/api)

## Configuration

The Lorcast API is **public** and requires **no authentication**. No API keys or tokens are needed.

> **Rate Limits:** Please keep requests to ~10/second (50–100 ms delay between calls). The server includes built-in rate limiting. Prices update once per day; gameplay data changes infrequently.

### VS Code MCP Configuration

Add to your `.vscode/mcp.json` (or workspace `settings.json` under `mcp.servers`):

```json
{
  "servers": {
    "lorcast": {
      "command": "python",
      "args": ["/path/to/lorcast/server.py"]
    }
  }
}
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python server.py
```

## Available Tools (9)

Every tool returns JSON. On success the response contains the API data; on failure it returns `{"error": "..."}`.

### Version

| Tool | Description |
|------|-------------|
| `show_version` | Server version, changelog, and API information |

### Sets

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `list_sets` | `GET /sets` | List all Lorcana card sets (standard and promotional) |
| `get_set` | `GET /sets/:id` | Get details of a specific set by code or ID |
| `get_set_cards` | `GET /sets/:id/cards` | Get all cards in a specific set |

### Cards

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `search_cards` | `GET /cards/search` | Full-text search with Lorcast syntax (set, rarity, ink, cost, type, etc.) |
| `get_card` | `GET /cards/:set/:number` | Get a specific card by set code and collector number |

### Images

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `get_card_image_uris` | `GET /cards/:set/:number` | Get CDN image URLs (small, normal, large) for a card |

### Prices

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `get_card_prices` | `GET /cards/:set/:number` | Get USD pricing (normal and foil) for a card |

### Convenience

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `get_cards_by_ink` | `GET /cards/search` | Search cards by ink color (Amber, Amethyst, Emerald, Ruby, Sapphire, Steel) |
| `get_cards_by_rarity` | `GET /cards/search` | Search cards by rarity (Common, Uncommon, Rare, Super_rare, Legendary, Enchanted, Promo) |

## Search Syntax

The `search_cards` tool supports the full [Lorcast search syntax](https://lorcast.com/docs/syntax). Some examples:

| Query | Description |
|-------|-------------|
| `elsa` | Find all cards named Elsa |
| `elsa set:1` | Elsa cards from The First Chapter |
| `elsa set:1 rarity:enchanted` | Enchanted Elsa from The First Chapter |
| `ink:amethyst cost:3` | Amethyst ink cards that cost 3 |
| `type:action` | All Action cards |
| `ink:ruby type:character` | Ruby Character cards |

## Card Model

Each card returned by the API includes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique card identifier |
| `name` | string | Card name |
| `version` | string | Card version/edition |
| `layout` | string | `normal` or `landscape` (Locations) |
| `cost` | integer | Ink cost to play |
| `inkwell` | boolean | Whether the card can be inked |
| `ink` | string | Ink color (Amber, Amethyst, Emerald, Ruby, Sapphire, Steel) |
| `type` | string[] | Card types (e.g., Character, Action, Song) |
| `classifications` | string[] | Character classifications (e.g., Floodborn, Hero) |
| `text` | string | Abilities and rules text |
| `strength` | integer | Strength attribute |
| `willpower` | integer | Willpower attribute |
| `lore` | integer | Lore attribute |
| `rarity` | string | Rarity level |
| `collector_number` | string | Number within its set |
| `prices` | object | USD pricing (`usd`, `usd_foil`) |
| `image_uris` | object | CDN URLs for card images |
| `set` | object | Set info (`id`, `code`, `name`) |

## Testing

```bash
python -m pytest test_server.py -v
```

## License

Lorcast uses trademarks and/or copyrights associated with Disney Lorcana TCG, used under Ravensburger's Community Code Policy. This project is not published, endorsed, or specifically approved by Disney or Ravensburger.
