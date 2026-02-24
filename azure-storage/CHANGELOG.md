# Azure Storage MCP Server Changelog

## [1.2.0] - 2026-02-12

### Changed
- **download_blob**: Reduced default expiry from 60 minutes to 5 minutes (principle of least privilege)
- **download_blob**: Reduced maximum expiry from 1440 minutes (24h) to 60 minutes (1h)
- Improved tool description and docstring with security architecture rationale (why SAS, why not raw blob URLs)

### Added
- `Content-Disposition: attachment` header in SAS token so browsers trigger a file download instead of trying to display the file inline
- URL-encoding of blob names to handle paths with special characters (spaces, parentheses, etc.)
- New tests for Content-Disposition header and URL encoding
- Expanded security documentation in README explaining the SAS-based download architecture

## [1.1.0] - 2026-02-12

### Added
- New `download_blob` tool to generate temporary SAS-based download URLs for individual blobs
- Support for configurable link expiry (1–1440 minutes)
- Automatic credential extraction from connection strings when account_name/account_key are not explicitly set
- Blob existence validation before generating download URLs
- Returns blob metadata (size, content type, last modified) alongside the download URL

## [1.0.0] - 2025-01-09

### Added
- Initial release of Azure Storage MCP Server
- Support for checking if Azure Blob Storage containers contain files
- Configuration via environment variables or JSON file
- Tools for listing configured containers
- Tools for checking all containers for blob presence
- Tools for checking specific containers
- Tools for listing blobs in containers with optional filtering
- Support for both connection strings and account key authentication
- Comprehensive error handling and logging
- Version and changelog display functionality

### Features
- `list_containers`: List all configured Azure Blob Storage containers
- `check_containers`: Check all configured containers for blob presence
- `check_container`: Check a specific container for blob presence
- `list_blobs`: List blobs in a specific container with optional prefix filtering
- `show_version`: Display current version and changelog

### Security
- Secrets are not logged or exposed in responses
- Support for multiple authentication methods
- Proper error handling for Azure API calls
