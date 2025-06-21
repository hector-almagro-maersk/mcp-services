# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2025-06-22

### Added
- **Configurable Edit Mode**: New optional `--edit-mode` flag to enable write operations
- `execute_write_query` tool for executing INSERT, UPDATE, DELETE, and DDL operations
- `create_table` tool for creating new tables with column definitions
- `drop_table` tool for dropping existing tables
- `update_data` tool for updating records in tables
- `insert_data` tool for inserting new records into tables
- `delete_data` tool for deleting records from tables
- Command-line argument parsing for edit mode configuration
- Enhanced error handling for write operations
- Transaction support for data modification operations

### Changed
- Server remains in read-only mode by default for security
- Enhanced tool descriptions to clarify read-only vs write capabilities
- Improved connection string validation and error messages
- Updated help text to include edit mode usage instructions

### Security
- Write operations only available when explicitly enabled via `--edit-mode` flag
- Maintained strict validation for read operations
- Added validation for write operations to prevent SQL injection
- Transaction rollback on error for data integrity

## [1.0.0] - 2025-06-21

### Added
- MCP (Model Context Protocol) server for SQL Server read-only operations
- Support for SQL Server connection via connection string
- `execute_query` tool for executing read-only SELECT queries
- `list_tables` tool to list all available database tables
- `describe_table` tool to get the structure of a specific table
- Strict security validation to prevent write operations
- Detection and blocking of multiple SQL statements
- Filtering of forbidden keywords (INSERT, UPDATE, DELETE, etc.)
- CTE (Common Table Expression) validation to ensure SELECT-only operations
- SQL comment blocking for security reasons
- Prevention of dangerous system functions (xp_cmdshell, sp_configure, etc.)
- Request timeout configured to 10 minutes (600,000 ms)
- Robust error handling with descriptive messages
- Automatic database connection when executing tools
- Input parameter validation with safe types

### Configuration
- TypeScript configured for ES2020 compilation
- Main dependencies: @modelcontextprotocol/sdk, mssql
- Build and development scripts with watch mode
- StdioServerTransport for MCP communication

### Security
- Implementation of multiple security validation layers
- Only SELECT queries allowed
- SQL injection prevention through strict validation
- Blocking of system operations and administrative functions
- Safe query parameterization where applicable

### Documentation
- README.md with installation and usage instructions
- Example configuration file (mcp-config-example.json)
- Security testing documentation (SECURITY_TESTS.md)
- Server test script (test-server.sh)

---

## Versioning Format

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality that is backwards compatible  
- **PATCH**: Backwards compatible bug fixes

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for removed features
- **Fixed** for bug fixes
- **Security** for security improvements
