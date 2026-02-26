# Changelog

## [1.0.0] - 2026-02-26

### Added
- Initial release of Lorcast MCP server for Disney Lorcana TCG data
- **Sets**: `list_sets`, `get_set`, `get_set_cards` — browse all Lorcana sets and their cards
- **Cards**: `search_cards`, `get_card` — full-text search with Lorcast syntax, precise card lookup by set/number
- **Images**: `get_card_image_uris` — retrieve CDN URLs for card images (small, normal, large)
- **Prices**: `get_card_prices` — USD pricing for normal and foil versions
- **Convenience**: `get_cards_by_ink`, `get_cards_by_rarity` — quick filters by ink color and rarity
- Built-in rate limiting (100 ms between requests) to respect Lorcast API guidelines
- Version and changelog display tool (`show_version`)
