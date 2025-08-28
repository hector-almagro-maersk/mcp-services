## [0.2.0] - 2025-08-27
### Changed
- BREAKING: `get_oncall` ad-hoc overrides parameter now expects a compact string format `Name:YYYY-MM-DD[,Name2:YYYY-MM-DD...]` instead of JSON.
- Added parser and validation for new overrides format (deduplicates, validates dates, preserves order).

### Deprecated
- JSON string / list / object input for `overrides` is no longer supported via the tool interface (still possible internally via persistent config JSON field).

## [0.1.0] - 2025-08-27
### Added
- Initial release of On-Call Rotation MCP server
- `get_oncall` tool for engineer lookup with rotation + overrides
- `show_version` tool with changelog parsing
- Configuration via env var or config.json
- Unit tests for rotation logic and overrides
