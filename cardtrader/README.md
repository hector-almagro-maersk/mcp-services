# CardTrader MCP Server

A Model Context Protocol (MCP) server that provides a complete bridge to the [CardTrader Full API v2](https://www.cardtrader.com/docs/api/full/reference). Every public API endpoint is exposed as an individual MCP tool with full documentation.

**API Base URL:** `https://api.cardtrader.com/api/v2`

## Configuration

The server requires a CardTrader API Bearer token. Obtain yours from **CardTrader → Settings → API → Full API App**.

### Option 1: Environment Variable (Recommended)

```bash
export MCP_CARDTRADER_TOKEN="your_api_token"
```

### Option 2: JSON Environment Variable

```bash
export MCP_CARDTRADER_CONFIG='{"api_token":"your_api_token"}'
```

### Option 3: Config File

Create a `config.json` file in the same directory as the server:

```json
{
  "api_token": "your_api_token"
}
```

### VS Code MCP Configuration

Add to your `.vscode/mcp.json` (or workspace `settings.json` under `mcp.servers`):

```json
{
  "servers": {
    "cardtrader": {
      "command": "python",
      "args": ["/path/to/cardtrader/server.py"],
      "env": {
        "MCP_CARDTRADER_TOKEN": "your_api_token"
      }
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

## Available Tools (37)

Every tool returns JSON. On success the response contains the API data; on failure it returns `{"error": "..."}`.

### Version

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `show_version` | — | Server version and recent changelog |

### Reference Data

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `get_app_info` | `GET /info` | Test auth and retrieve app info |
| `list_games` | `GET /games` | List all available games (Magic, Lorcana, Pokémon, etc.) |
| `list_categories` | `GET /categories` | List item categories, optionally filtered by game |
| `list_expansions` | `GET /expansions` | List all expansions, optionally filtered by game |
| `list_blueprints` | `GET /blueprints/export` | List all blueprints (item models) in an expansion |

### Marketplace

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `list_marketplace_products` | `GET /marketplace/products` | Browse products for sale (cheapest 25 per blueprint) |
| `get_cart` | `GET /cart` | View current shopping cart |
| `add_to_cart` | `POST /cart/add` | Add a product to the cart |
| `remove_from_cart` | `POST /cart/remove` | Remove a product from the cart |
| `purchase_cart` | `POST /cart/purchase` | Purchase everything in the cart |
| `list_shipping_methods` | `GET /shipping_methods` | Shipping options from a seller to you |

### Wishlists

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `list_wishlists` | `GET /wishlists` | List your wishlists (paginated) |
| `get_wishlist` | `GET /wishlists/:id` | Full wishlist details |
| `create_wishlist` | `POST /wishlists` | Create a wishlist (structured items or MTGA text deck) |
| `delete_wishlist` | `DELETE /wishlists/:id` | Delete a wishlist |

### Inventory Management

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `list_my_expansions` | `GET /expansions/export` | Expansions you have products in |
| `list_my_products` | `GET /products/export` | Your products for sale |
| `create_product` | `POST /products` | Create (list) a product for sale |
| `update_product` | `PUT /products/:id` | Update product price/quantity/properties |
| `delete_product` | `DELETE /products/:id` | Delete a product |
| `increment_product` | `POST /products/:id/increment` | Increment or decrement quantity |
| `remove_product_image` | `DELETE /products/:id/upload_image` | Remove product image |

### Batch Operations

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `batch_create_products` | `POST /products/bulk_create` | Create multiple products (async) |
| `batch_update_products` | `POST /products/bulk_update` | Update multiple products (async) |
| `batch_delete_products` | `POST /products/bulk_destroy` | Delete multiple products (async) |
| `get_job_status` | `GET /jobs/:uuid` | Check batch job progress |

### CSV Import

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `get_csv_import_status` | `GET /product_imports/:id` | CSV import status |
| `get_csv_import_skipped` | `GET /product_imports/:id/skipped` | Skipped rows from CSV import |

> **Note:** CSV upload (`POST /product_imports`) and image upload (`POST /products/:id/upload_image`) require multipart form data and should be done via the CardTrader website or a direct HTTP client.

### Order Management

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `list_orders` | `GET /orders` | List orders (paginated, filterable) |
| `get_order` | `GET /orders/:id` | Full order details |
| `set_tracking_code` | `PUT /orders/:id/tracking_code` | Set tracking number |
| `ship_order` | `PUT /orders/:id/ship` | Mark order as shipped |
| `request_cancellation` | `PUT /orders/:id/request-cancellation` | Request cancellation |
| `confirm_cancellation` | `PUT /orders/:id/confirm-cancellation` | Confirm a cancellation request |

### CardTrader Zero Box

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `list_ct0_box_items` | `GET /ct0_box_items` | List items in your CT Zero box |
| `get_ct0_box_item` | `GET /ct0_box_items/:id` | Single CT Zero box item details |

## Example Workflows

### Browse and buy a card

```
1. list_games                                → find the game ID for "Disney Lorcana"
2. list_expansions(game_id=7)                → find expansion ID for "The First Chapter"
3. list_blueprints(expansion_id=3469)        → find blueprint ID for the card you want
4. list_marketplace_products(blueprint_id=X) → see cheapest listings
5. add_to_cart(product_id=Y, quantity=1)     → add to cart
6. purchase_cart                             → buy it
```

### Sell your collection

```
1. list_blueprints(expansion_id=3469)        → find blueprint IDs for your cards
2. create_product(blueprint_id=X, price=5.0, quantity=2)  → list a card
   OR
   batch_create_products(products='[...]')   → list many cards at once
3. get_job_status(uuid="...")                → check batch progress
```

### Manage wishlists

```
1. list_games                                → get game_id
2. create_wishlist(name="Wants", game_id=7, items='[{"blueprint_id":123,"quantity":1}]')
3. list_wishlists                            → see all wishlists
4. delete_wishlist(wishlist_id=456)           → remove a wishlist
```

## Rate Limits

The CardTrader API enforces:
- **General:** 200 requests per 10 seconds
- **Marketplace products:** 10 requests per second
- **Jobs status:** 1 request per second

The server does not implement automatic throttling — be mindful of rapid successive calls.

## API Reference

Full API documentation: https://www.cardtrader.com/docs/api/full/reference
