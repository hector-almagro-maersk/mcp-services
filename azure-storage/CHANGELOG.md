# Azure Storage MCP Server Changelog

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
