"""
CardTrader MCP Server — Full API Bridge
========================================
A Model Context Protocol (MCP) server that exposes every endpoint of the
CardTrader Full API v2 as an MCP tool.

Base URL: https://api.cardtrader.com/api/v2
API Docs: https://www.cardtrader.com/docs/api/full/reference

Authentication
--------------
Set one of:
  - MCP_CARDTRADER_TOKEN env var (bearer token string)
  - MCP_CARDTRADER_CONFIG env var (JSON: {"api_token": "..."})
  - config.json next to this file   (JSON: {"api_token": "..."})
"""

import os
import re
import json
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional, List
import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _get_config() -> Dict[str, str]:
    """Load CardTrader API token from env vars or config.json."""
    config_str = os.environ.get("MCP_CARDTRADER_CONFIG")
    if config_str:
        try:
            return json.loads(config_str)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in MCP_CARDTRADER_CONFIG: {e}")

    token = os.environ.get("MCP_CARDTRADER_TOKEN")
    if token:
        return {"api_token": token}

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)

    raise Exception(
        "No CardTrader configuration found. "
        "Set MCP_CARDTRADER_TOKEN, MCP_CARDTRADER_CONFIG, or create config.json"
    )


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

BASE_URL = "https://api.cardtrader.com/api/v2"

_client_headers: Optional[Dict[str, str]] = None


def _headers() -> Dict[str, str]:
    global _client_headers
    if _client_headers is None:
        token = _get_config().get("api_token", "")
        if not token:
            raise Exception("api_token missing from configuration")
        _client_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    return _client_headers


def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    r = requests.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers=_headers(),
        params=params,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def _post(path: str, body: Optional[Any] = None) -> Any:
    r = requests.post(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers=_headers(),
        json=body,
        timeout=60,
    )
    r.raise_for_status()
    return r.json() if r.text else {"result": "ok"}


def _put(path: str, body: Optional[Any] = None) -> Any:
    r = requests.put(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers=_headers(),
        json=body,
        timeout=60,
    )
    r.raise_for_status()
    return r.json() if r.text else {"result": "ok"}


def _delete(path: str) -> Any:
    r = requests.delete(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers=_headers(),
        timeout=60,
    )
    r.raise_for_status()
    return r.json() if r.text else {"result": "ok"}


def _ok(data: Any) -> str:
    return json.dumps(data, indent=2)


def _err(msg: Any) -> str:
    return json.dumps({"error": str(msg)})


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP("cardtrader")


# ── Version ────────────────────────────────────────────────────────────────

@mcp.tool()
def show_version() -> str:
    """Show the CardTrader MCP server version and recent changelog."""
    try:
        base = os.path.dirname(__file__)
        version = _read_file(os.path.join(base, "VERSION")).strip()
        changelog = _read_file(os.path.join(base, "CHANGELOG.md"))
        return _ok({
            "version": version,
            "recent_changes": _parse_changelog(changelog)[:3],
        })
    except Exception as e:
        return _err(e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  REFERENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ── App Info ───────────────────────────────────────────────────────────────

@mcp.tool()
def get_app_info() -> str:
    """
    GET /info — Test authentication and retrieve app information.

    Use this call to verify that your API token is valid.

    Returns the App object:
      - id (int): Your App unique identifier.
      - name (str): The name of your App.
      - shared_secret (hex): Used to verify webhook signature authenticity.
      - user_id (int): Your User unique identifier.
    """
    try:
        return _ok(_get("info"))
    except Exception as e:
        return _err(e)


# ── Games ──────────────────────────────────────────────────────────────────

@mcp.tool()
def list_games() -> str:
    """
    GET /games — List all available games on CardTrader.

    A Game identifies a family of sellable items (e.g. "Magic: the Gathering",
    "Disney Lorcana", "Pokémon").

    Returns an array of Game objects:
      - id (int): Unique Game identifier.
      - name (str): Internal game name.
      - display_name (str): Human-readable game name.
    """
    try:
        raw = _get("games")
        # /games endpoint may wrap results in {"array": [...]}
        games = raw["array"] if isinstance(raw, dict) and "array" in raw else raw
        return _ok(games)
    except Exception as e:
        return _err(e)


# ── Categories ─────────────────────────────────────────────────────────────

@mcp.tool()
def list_categories(game_id: Optional[int] = None) -> str:
    """
    GET /categories — List available categories.

    A Category groups similar items inside a Game (e.g. "Single Cards",
    "Booster Box", "Tokens", "Dice"). There are approximately thirty
    Categories across all games.

    Args:
        game_id: Optional. Filter results by game.

    Returns an array of Category objects:
      - id (int): Unique Category identifier.
      - name (str): Category name.
      - game_id (int): The Game this Category belongs to.
      - properties ([Property]): Accepted properties for items in this category.
    """
    try:
        params: Dict[str, Any] = {}
        if game_id is not None:
            params["game_id"] = game_id
        return _ok(_get("categories", params or None))
    except Exception as e:
        return _err(e)


# ── Expansions ─────────────────────────────────────────────────────────────

@mcp.tool()
def list_expansions(game_id: Optional[int] = None) -> str:
    """
    GET /expansions — List all expansions.

    An Expansion is a specific set/release within a Game (e.g. "The First
    Chapter" for Lorcana, "Core Set 2020" for Magic).

    Args:
        game_id: Optional. If provided, only expansions for this game are
                 returned (client-side filter; the API returns all).

    Returns an array of Expansion objects:
      - id (int): Unique Expansion identifier.
      - game_id (int): The Game this Expansion belongs to.
      - code (str): Short code (3-4 chars) identifying the expansion.
      - name (str): Full expansion name.
    """
    try:
        data = _get("expansions")
        if game_id is not None:
            data = [e for e in data if e.get("game_id") == game_id]
        return _ok(data)
    except Exception as e:
        return _err(e)


# ── Blueprints ─────────────────────────────────────────────────────────────

@mcp.tool()
def list_blueprints(expansion_id: int) -> str:
    """
    GET /blueprints/export — List all blueprints in an expansion.

    A Blueprint represents an item model that can be bought or sold. Each
    reprint of the same card in a different expansion is a separate Blueprint.

    Args:
        expansion_id: Required. The Expansion ID (from list_expansions).
                      If invalid, the API responds with 404.

    Returns an array of Blueprint objects:
      - id (int): Unique Blueprint identifier.
      - name (str): Blueprint name.
      - version (str|null): Version string (almost always null).
      - game_id (int): Game ID.
      - category_id (int): Category ID.
      - expansion_id (int): Expansion ID.
      - image_url (str): URL to the item image.
      - editable_properties ([Property]): Properties you can set when selling.
      - scryfall_id (str|null): Scryfall identifier.
      - card_market_ids ([int]): Cardmarket identifiers.
      - tcg_player_id (str|null): TCGplayer identifier.
    """
    try:
        return _ok(_get("blueprints/export", {"expansion_id": expansion_id}))
    except Exception as e:
        return _err(e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MARKETPLACE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ── Marketplace Products ───────────────────────────────────────────────────

@mcp.tool()
def list_marketplace_products(
    expansion_id: Optional[int] = None,
    blueprint_id: Optional[int] = None,
    foil: Optional[bool] = None,
    language: Optional[str] = None,
) -> str:
    """
    GET /marketplace/products — List products for sale on the marketplace.

    You must provide either expansion_id OR blueprint_id. Returns the cheapest
    25 products per blueprint. Results are lightly cached.

    Rate limit: 10 requests/second.

    Args:
        expansion_id: Filter by expansion.
        blueprint_id: Filter by specific blueprint.
        foil: Optional boolean filter for foil products.
        language: Optional 2-letter locale (e.g. "en", "it", "fr").

    Returns an object keyed by blueprint_id (string). Each value is an array
    of up to 25 Product objects:
      - id (int): Product ID (use to add to cart).
      - blueprint_id (int), name_en (str), quantity (int).
      - price: {cents (int), currency (str)}.
      - description (str), properties_hash (object).
      - expansion: {id, code, name_en}.
      - user: {id, username, can_sell_via_hub, country_code, user_type,
               max_sellable_in24h_quantity}.
      - graded (bool), on_vacation (bool), bundle_size (int).
    """
    if expansion_id is None and blueprint_id is None:
        return _err("Provide either expansion_id or blueprint_id.")
    try:
        params: Dict[str, Any] = {}
        if expansion_id is not None:
            params["expansion_id"] = expansion_id
        if blueprint_id is not None:
            params["blueprint_id"] = blueprint_id
        if foil is not None:
            params["foil"] = str(foil).lower()
        if language is not None:
            params["language"] = language
        return _ok(_get("marketplace/products", params))
    except Exception as e:
        return _err(e)


# ── Cart ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_cart() -> str:
    """
    GET /cart — Get the current shopping cart.

    The Cart consists of subcarts — one per seller plus one for CardTrader
    Zero. Each subcart contains cart_items (the products you are purchasing).
    Unavailable products are automatically removed from the response.

    Returns the Cart object:
      - id (int), created_at, updated_at.
      - subcarts []: Each has id, cart_items [], subtotal, shipping_cost,
        safeguard_fee_amount, ct_zero_fee_amount,
        payment_method_fee_percentage_amount,
        payment_method_fee_fixed_amount.
      - billing_address, shipping_address (Address|null).
    """
    try:
        return _ok(_get("cart"))
    except Exception as e:
        return _err(e)


@mcp.tool()
def add_to_cart(
    product_id: int,
    quantity: int,
    via_cardtrader_zero: bool = True,
    billing_address: Optional[str] = None,
    shipping_address: Optional[str] = None,
) -> str:
    """
    POST /cart/add — Add a product to the cart. Returns the updated Cart.

    Args:
        product_id: The Product ID (from marketplace listings).
        quantity: Number of items to add.
        via_cardtrader_zero: Buy via CardTrader Zero (true) or direct (false).
        billing_address: Optional JSON string with address object:
            {name, street, zip, city, state_or_province, country_code}.
            If specified multiple times, the last one is used.
        shipping_address: Optional JSON string (same keys as billing).

    Returns the updated Cart object.
    """
    try:
        body: Dict[str, Any] = {
            "product_id": product_id,
            "quantity": quantity,
            "via_cardtrader_zero": via_cardtrader_zero,
        }
        if billing_address:
            body["billing_address"] = json.loads(billing_address)
        if shipping_address:
            body["shipping_address"] = json.loads(shipping_address)
        return _ok(_post("cart/add", body))
    except Exception as e:
        return _err(e)


@mcp.tool()
def remove_from_cart(product_id: int, quantity: int) -> str:
    """
    POST /cart/remove — Remove a product from the cart.

    Args:
        product_id: The Product ID to remove.
        quantity: Number to remove. Cannot be lower than the number in cart.

    Returns the updated Cart object.
    """
    try:
        return _ok(_post("cart/remove", {
            "product_id": product_id,
            "quantity": quantity,
        }))
    except Exception as e:
        return _err(e)


@mcp.tool()
def purchase_cart() -> str:
    """
    POST /cart/purchase — Finalize and purchase the cart.

    You must have sufficient wallet credit or a credit/debit card added to
    your payment methods (add via the CardTrader website GUI).

    Returns the purchased Cart object on success, or an error (e.g. missing
    payment method).
    """
    try:
        return _ok(_post("cart/purchase"))
    except Exception as e:
        return _err(e)


# ── Shipping Methods ───────────────────────────────────────────────────────

@mcp.tool()
def list_shipping_methods(username: str) -> str:
    """
    GET /shipping_methods — List shipping methods from a seller to you.

    Args:
        username: The seller's username (from marketplace product user field).
            Spaces become '+', special chars must be URL-encoded.
            E.g. "ct connect" → "ct+connect".

    Returns an array of ShippingMethod objects:
      - id (int), name (str), parcel (bool), tracked (bool).
      - tracking_link (str|null): URL with {code} placeholder.
      - min_estimate_shipping_days, max_estimate_shipping_days (int|null).
      - free_shipping_threshold_quantity (int|null).
      - free_shipping_threshold_price (Money|null).
      - max_cart_subtotal_price (Money|null).
      - shipping_method_costs []: {from_grams, to_grams, price, formatted_price}.
    """
    try:
        return _ok(_get("shipping_methods", {"username": username}))
    except Exception as e:
        return _err(e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WISHLISTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
def list_wishlists(
    game_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
) -> str:
    """
    GET /wishlists — List your wishlists (paginated).

    Args:
        game_id: Optional. Filter wishlists by game.
        page: Page number, starting from 1 (default 1).
        limit: Items per page, 1-100 (default 20).

    Returns an array of wishlist summaries:
      - id (int), name (str), game_id (int), public (bool).
      - created_at (datetime), updated_at (datetime).
    """
    try:
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if game_id is not None:
            params["game_id"] = game_id
        return _ok(_get("wishlists", params))
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_wishlist(wishlist_id: int) -> str:
    """
    GET /wishlists/:id — Retrieve full details of a specific wishlist.

    Args:
        wishlist_id: The wishlist ID.

    Returns the wishlist object:
      - id (int), name (str), game_id (int), public (bool).
      - created_at, updated_at (datetime).
      - items [DeckItem]: Each has quantity, meta_name, expansion_code,
        collector_number, language, condition, foil, reverse, first_edition.
    """
    try:
        return _ok(_get(f"wishlists/{wishlist_id}"))
    except Exception as e:
        return _err(e)


@mcp.tool()
def create_wishlist(
    name: str,
    game_id: int,
    items: Optional[str] = None,
    items_text: Optional[str] = None,
    public: bool = False,
) -> str:
    """
    POST /wishlists — Create a new wishlist.

    You must provide either 'items' (structured JSON) or 'items_text'
    (MTGA-format text deck). Lines in items_text that don't match a
    blueprint are silently ignored.

    Args:
        name: Wishlist name (e.g. "My Lorcana Wants").
        game_id: The CardTrader game ID (from list_games).
        items: JSON array of DeckItem objects. Each can have:
            - blueprint_id (int): Shortcut to auto-set meta_name & expansion_code.
            - quantity (int).
            - meta_name (str): Card identifier across editions.
            - expansion_code (str).
            - collector_number (str).
            - language (str), condition (str), foil (str).
            - reverse (str), first_edition (bool).
        items_text: Deck in MTGA text format (alternative to items).
        public: Whether the wishlist is publicly visible (default false).

    Returns the created wishlist object.
    """
    try:
        deck: Dict[str, Any] = {
            "game_id": game_id,
            "name": name,
            "public": public,
        }
        if items is not None:
            deck_items = json.loads(items)
            if not isinstance(deck_items, list):
                return _err("items must be a JSON array")
            deck["deck_items_attributes"] = deck_items
        elif items_text is not None:
            deck["deck_items_from_text_deck"] = items_text
        else:
            return _err("Provide either 'items' (JSON array) or 'items_text'.")
        return _ok(_post("wishlists", {"deck": deck}))
    except json.JSONDecodeError:
        return _err("Invalid JSON in items parameter.")
    except Exception as e:
        return _err(e)


@mcp.tool()
def delete_wishlist(wishlist_id: int) -> str:
    """
    DELETE /wishlists/:id — Delete a wishlist.

    Args:
        wishlist_id: The wishlist ID to delete.
    """
    try:
        return _ok(_delete(f"wishlists/{wishlist_id}"))
    except Exception as e:
        return _err(e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INVENTORY MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ── My Expansions ──────────────────────────────────────────────────────────

@mcp.tool()
def list_my_expansions() -> str:
    """
    GET /expansions/export — List expansions you have products in.

    Returns only the expansions for which you currently have inventory.

    Returns an array of Expansion objects:
      - id (int), game_id (int), code (str), name (str).
    """
    try:
        return _ok(_get("expansions/export"))
    except Exception as e:
        return _err(e)


# ── My Products ────────────────────────────────────────────────────────────

@mcp.tool()
def list_my_products(
    expansion_id: Optional[int] = None,
    blueprint_id: Optional[int] = None,
) -> str:
    """
    GET /products/export — List your products for sale.

    WARNING: This call may take several seconds on large collections.
    Ensure your timeout is 120-180s. Optionally filter by expansion or
    blueprint.

    Args:
        expansion_id: Optional. Only products in this expansion.
        blueprint_id: Optional. Only products for this blueprint.

    Returns an array of Product objects:
      - id (int), name_en (str), quantity (int), description (str).
      - price_cents (int), price_currency (str).
      - game_id, category_id, blueprint_id (int).
      - properties_hash (object), user_id (int).
      - graded (str), tag (str), user_data_field (str).
      - bundle_size (int), bundled_quantity (int).
      - uploaded_images ([]).
    """
    try:
        params: Dict[str, Any] = {}
        if expansion_id is not None:
            params["expansion_id"] = expansion_id
        if blueprint_id is not None:
            params["blueprint_id"] = blueprint_id
        return _ok(_get("products/export", params or None))
    except Exception as e:
        return _err(e)


# ── Single Product Operations ──────────────────────────────────────────────

@mcp.tool()
def create_product(
    blueprint_id: int,
    price: float,
    quantity: int,
    description: Optional[str] = None,
    properties: Optional[str] = None,
    user_data_field: Optional[str] = None,
    graded: Optional[bool] = None,
    error_mode: Optional[str] = None,
) -> str:
    """
    POST /products — Create (sell) a single product.

    If a product with the same blueprint and properties already exists,
    the quantity is incremented rather than creating a duplicate.

    Args:
        blueprint_id: The Blueprint ID of the item to sell.
        price: Price in your currency (e.g. 3.50).
        quantity: Number of items to sell.
        description: Optional text visible to buyers.
        properties: Optional JSON object string of properties. Keys are
            property names (e.g. "condition", "mtg_language", "mtg_foil"),
            values must be from the blueprint's editable_properties
            possible_values. Default condition is "Near Mint".
        user_data_field: Optional private metadata (not visible to buyers).
        graded: Whether the product is graded.
        error_mode: "strict" to fail on invalid properties, or omit to
            auto-correct to defaults.

    Returns: {result, warnings, resource}.
    """
    try:
        body: Dict[str, Any] = {
            "blueprint_id": blueprint_id,
            "price": price,
            "quantity": quantity,
        }
        if description is not None:
            body["description"] = description
        if properties is not None:
            body["properties"] = json.loads(properties)
        if user_data_field is not None:
            body["user_data_field"] = user_data_field
        if graded is not None:
            body["graded"] = graded
        if error_mode is not None:
            body["error_mode"] = error_mode
        return _ok(_post("products", body))
    except Exception as e:
        return _err(e)


@mcp.tool()
def update_product(
    product_id: int,
    price: Optional[float] = None,
    quantity: Optional[int] = None,
    description: Optional[str] = None,
    properties: Optional[str] = None,
    user_data_field: Optional[str] = None,
    graded: Optional[bool] = None,
    error_mode: Optional[str] = None,
) -> str:
    """
    PUT /products/:id — Update an existing product.

    Only provided fields are changed; omitted fields remain untouched.

    Args:
        product_id: The Product ID to update.
        price: New price in your currency.
        quantity: New quantity.
        description: New description.
        properties: JSON object string of properties to update.
        user_data_field: Private metadata text.
        graded: Graded flag.
        error_mode: "strict" or omit for auto-correction.

    Returns: {result, warnings, resource}.
    """
    try:
        body: Dict[str, Any] = {}
        if price is not None:
            body["price"] = price
        if quantity is not None:
            body["quantity"] = quantity
        if description is not None:
            body["description"] = description
        if properties is not None:
            body["properties"] = json.loads(properties)
        if user_data_field is not None:
            body["user_data_field"] = user_data_field
        if graded is not None:
            body["graded"] = graded
        if error_mode is not None:
            body["error_mode"] = error_mode
        return _ok(_put(f"products/{product_id}", body))
    except Exception as e:
        return _err(e)


@mcp.tool()
def delete_product(product_id: int) -> str:
    """
    DELETE /products/:id — Delete a product regardless of its quantity.

    Prefer update_product to modify attributes instead of deleting and
    recreating.

    Args:
        product_id: The Product ID to delete.

    Returns: {result, warnings, resource}.
    """
    try:
        return _ok(_delete(f"products/{product_id}"))
    except Exception as e:
        return _err(e)


@mcp.tool()
def increment_product(product_id: int, delta_quantity: int) -> str:
    """
    POST /products/:id/increment — Increment or decrement product quantity.

    Price and other attributes remain unchanged. If the resulting quantity
    reaches 0 or below, the product is deleted.

    Args:
        product_id: The Product ID.
        delta_quantity: Positive to increase, negative to decrease.

    Returns: {result, warnings, resource}.
    """
    try:
        return _ok(_post(
            f"products/{product_id}/increment",
            {"delta_quantity": delta_quantity},
        ))
    except Exception as e:
        return _err(e)


@mcp.tool()
def remove_product_image(product_id: int) -> str:
    """
    DELETE /products/:id/upload_image — Remove the image from a product.

    Args:
        product_id: The Product ID whose image to remove.
    """
    try:
        return _ok(_delete(f"products/{product_id}/upload_image"))
    except Exception as e:
        return _err(e)


# ── Batch Product Operations ──────────────────────────────────────────────

@mcp.tool()
def batch_create_products(products: str) -> str:
    """
    POST /products/bulk_create — Create multiple products asynchronously.

    Returns a job UUID. Check progress with get_job_status.

    Args:
        products: JSON array of product objects. Each must have:
            - blueprint_id (int, mandatory)
            - price (float, mandatory)
            - quantity (int, mandatory)
            Optional: description (str), error_mode ("strict"),
            user_data_field (str), properties (object), graded (bool).

    Returns: {job: "<uuid>"}.
    """
    try:
        items = json.loads(products)
        if not isinstance(items, list):
            return _err("products must be a JSON array.")
        return _ok(_post("products/bulk_create", {"products": items}))
    except json.JSONDecodeError:
        return _err("Invalid JSON in products parameter.")
    except Exception as e:
        return _err(e)


@mcp.tool()
def batch_update_products(products: str) -> str:
    """
    POST /products/bulk_update — Update multiple products asynchronously.

    Returns a job UUID. Check progress with get_job_status.

    Args:
        products: JSON array of product objects. Each must have:
            - id (int, mandatory)
            Optional: price, quantity, description, error_mode,
            user_data_field, properties (object), graded (bool).

    Returns: {job: "<uuid>"}.
    """
    try:
        items = json.loads(products)
        if not isinstance(items, list):
            return _err("products must be a JSON array.")
        return _ok(_post("products/bulk_update", {"products": items}))
    except json.JSONDecodeError:
        return _err("Invalid JSON in products parameter.")
    except Exception as e:
        return _err(e)


@mcp.tool()
def batch_delete_products(product_ids: str) -> str:
    """
    POST /products/bulk_destroy — Delete multiple products asynchronously.

    Returns a job UUID. Check progress with get_job_status.

    Args:
        product_ids: Either a JSON array of objects with "id" key
            (e.g. '[{"id": 123}, {"id": 456}]') or comma-separated IDs
            (e.g. "123,456,789").

    Returns: {job: "<uuid>"}.
    """
    try:
        try:
            items = json.loads(product_ids)
        except json.JSONDecodeError:
            items = [{"id": int(x.strip())} for x in product_ids.split(",")]
        if not isinstance(items, list):
            return _err("product_ids must be a JSON array or comma-separated IDs.")
        return _ok(_post("products/bulk_destroy", {"products": items}))
    except Exception as e:
        return _err(e)


# ── Jobs ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_job_status(uuid: str) -> str:
    """
    GET /jobs/:uuid — Check status of an async batch product operation.

    Rate limit: 1 request/second.

    Args:
        uuid: The job UUID returned by a batch operation.

    Returns the Job object:
      - uuid (str), state ("pending"|"running"|"unprocessable"|"completed").
      - spawned_children (int): Number of operations.
      - stats: {ok (int), warning (int), error (int)}.
      - results []: Each has result, job_index, product_id, and optionally
        errors or warnings.
    """
    try:
        return _ok(_get(f"jobs/{uuid}"))
    except Exception as e:
        return _err(e)


# ── CSV Import ─────────────────────────────────────────────────────────────

@mcp.tool()
def get_csv_import_status(import_id: int) -> str:
    """
    GET /product_imports/:id — Check the status of a CSV product import.

    Note: CSV uploads (POST /product_imports) require multipart form data
    and should be done via the CardTrader website or a direct HTTP client.

    Args:
        import_id: The import ID returned by the CSV upload.

    Returns:
      - id, count, imported_count, skipped_count.
      - create_count, update_count, delete_count.
      - error (str|null), sync_started_at, sync_ended_at.
      - csv_filename (str), csv_size (int).
    """
    try:
        return _ok(_get(f"product_imports/{import_id}"))
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_csv_import_skipped(import_id: int) -> str:
    """
    GET /product_imports/:id/skipped — Get skipped rows from a CSV import.

    Returns the CSV content of rows that failed to import.

    Args:
        import_id: The import ID.
    """
    try:
        return _ok(_get(f"product_imports/{import_id}/skipped"))
    except Exception as e:
        return _err(e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ORDER MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
def list_orders(
    page: int = 1,
    limit: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    from_id: Optional[int] = None,
    to_id: Optional[int] = None,
    state: Optional[str] = None,
    order_as: Optional[str] = None,
    sort: Optional[str] = None,
) -> str:
    """
    GET /orders — List your orders (paginated).

    Order lifecycle states:
      Standard: paid → sent → arrived → done
      CT Zero:  hub_pending → paid → sent → arrived → done
      Special:  request_for_cancel, canceled, lost

    Args:
        page: Page number (default 1).
        limit: 1-100 items per page (default 20).
        from_date: Start date filter "YYYY-MM-DD" (default 1970-01-01).
        to_date: End date filter "YYYY-MM-DD" (default today).
        from_id: Exclude orders with id <= this value.
        to_id: Exclude orders with id > this value.
        state: Filter by state (e.g. "paid", "sent", "hub_pending").
        order_as: "seller" or "buyer".
        sort: "id.asc", "id.desc", "date.asc", "date.desc" (default
              "date.desc").

    Returns an array of Order objects, each containing:
      - id, code, transaction_code, via_cardtrader_zero.
      - seller/buyer (User), order_as, state, size.
      - paid_at, sent_at, cancelled_at, credit_added_to_seller_at.
      - buyer_total, seller_total, fee_amount, seller_fee_amount (Money).
      - packing_number, presale, order_items [].
      - order_shipping_address, order_billing_address, order_shipping_method.
    """
    try:
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if from_id is not None:
            params["from_id"] = from_id
        if to_id is not None:
            params["to_id"] = to_id
        if state:
            params["state"] = state
        if order_as:
            params["order_as"] = order_as
        if sort:
            params["sort"] = sort
        return _ok(_get("orders", params))
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_order(order_id: int) -> str:
    """
    GET /orders/:id — Get full details of a single order.

    Args:
        order_id: The Order ID.

    Returns the full Order object including order_items. Same structure as
    list_orders but for a single order.
    """
    try:
        return _ok(_get(f"orders/{order_id}"))
    except Exception as e:
        return _err(e)


@mcp.tool()
def set_tracking_code(order_id: int, tracking_code: str) -> str:
    """
    PUT /orders/:id/tracking_code — Set a tracking code for an order.

    For CardTrader Zero orders, set the tracking code BEFORE shipping.
    Only the seller can set the tracking code.

    Args:
        order_id: The Order ID.
        tracking_code: The tracking number string.

    Returns the updated Order object.
    """
    try:
        return _ok(_put(
            f"orders/{order_id}/tracking_code",
            {"tracking_code": tracking_code},
        ))
    except Exception as e:
        return _err(e)


@mcp.tool()
def ship_order(order_id: int) -> str:
    """
    PUT /orders/:id/ship — Mark an order as shipped.

    The order must be in a valid state for shipping. Returns an error if
    the state transition is not allowed.

    Args:
        order_id: The Order ID.

    Returns the updated Order object.
    """
    try:
        return _ok(_put(f"orders/{order_id}/ship"))
    except Exception as e:
        return _err(e)


@mcp.tool()
def request_cancellation(
    order_id: int,
    cancel_explanation: str,
    relist_if_cancelled: bool = False,
) -> str:
    """
    PUT /orders/:id/request-cancellation — Request order cancellation.

    Sends a cancellation request to the other party. Allowed when the order
    is in "paid" or "sent" state.

    Args:
        order_id: The Order ID.
        cancel_explanation: Reason for cancellation (minimum 50 characters).
        relist_if_cancelled: Re-list products if cancellation is confirmed
                             (default false).

    Returns the updated Order object.
    """
    try:
        body: Dict[str, Any] = {
            "cancel_explanation": cancel_explanation,
            "relist_if_cancelled": relist_if_cancelled,
        }
        return _ok(_put(f"orders/{order_id}/request-cancellation", body))
    except Exception as e:
        return _err(e)


@mcp.tool()
def confirm_cancellation(
    order_id: int,
    relist_if_cancelled: bool = False,
) -> str:
    """
    PUT /orders/:id/confirm-cancellation — Confirm an order cancellation.

    Only available if a cancellation has been requested by the other party.

    Args:
        order_id: The Order ID.
        relist_if_cancelled: Re-list products after cancellation (default false).
                             Only applicable if you are the seller.

    Returns the updated Order object.
    """
    try:
        body: Dict[str, Any] = {
            "relist_if_cancelled": relist_if_cancelled,
        }
        return _ok(_put(f"orders/{order_id}/confirm-cancellation", body))
    except Exception as e:
        return _err(e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CARDTRADER ZERO BOX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
def list_ct0_box_items() -> str:
    """
    GET /ct0_box_items — List your CardTrader Zero box items.

    CT0 Box Items are products purchased via CardTrader Zero that have not
    yet been shipped directly to you.

    Returns an array of CT0 Box Item objects:
      - id (int), quantity: {ok, pending, missing}.
      - seller (User), product_id, blueprint_id, category_id, game_id.
      - name (str), expansion (str), bundle_size (int).
      - description (str), graded (str|false).
      - properties (object), buyer_price (Money), formatted_price (str).
      - mkm_id, tcg_player_id, scryfall_id (str|null).
      - presale (bool|null), presale_ended_at, paid_at.
      - estimated_arrived_at, arrived_at, cancelled_at (datetime|null).
    """
    try:
        return _ok(_get("ct0_box_items"))
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_ct0_box_item(item_id: int) -> str:
    """
    GET /ct0_box_items/:id — Get details of a single CT0 box item.

    Args:
        item_id: The CT0 Box Item ID.

    Returns the same structure as list_ct0_box_items, for a single item.
    """
    try:
        return _ok(_get(f"ct0_box_items/{item_id}"))
    except Exception as e:
        return _err(e)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
