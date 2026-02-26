# Changelog

## [1.0.0] - 2026-02-26

### Added
- Initial release of CardTrader MCP server — full API v2 bridge
- Every public CardTrader API endpoint exposed as an individual MCP tool (37 tools)
- **Reference**: `get_app_info`, `list_games`, `list_categories`, `list_expansions`, `list_blueprints`
- **Marketplace**: `list_marketplace_products`, `get_cart`, `add_to_cart`, `remove_from_cart`, `purchase_cart`, `list_shipping_methods`
- **Wishlists**: `list_wishlists`, `get_wishlist`, `create_wishlist`, `delete_wishlist` — supports all games and MTGA text deck import
- **Inventory**: `list_my_expansions`, `list_my_products`, `create_product`, `update_product`, `delete_product`, `increment_product`, `remove_product_image`
- **Batch operations**: `batch_create_products`, `batch_update_products`, `batch_delete_products`, `get_job_status`
- **CSV import**: `get_csv_import_status`, `get_csv_import_skipped`
- **Orders**: `list_orders`, `get_order`, `set_tracking_code`, `ship_order`, `request_cancellation`, `confirm_cancellation`
- **CT Zero Box**: `list_ct0_box_items`, `get_ct0_box_item`
- Bearer token authentication via environment variable, JSON env var, or config file
- Comprehensive error handling with JSON error responses
- Version and changelog display tool (`show_version`)
