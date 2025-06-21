# MCP SQL Server Server

A simple MCP (Model Context Protocol) server for performing read-only and configurable write operations on SQL Server databases.

## Version

Current version: **1.1.0**

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Features

- ✅ **Read-only by default**: Only allows `SELECT` queries unless edit mode is enabled
- ✅ **Configurable edit mode**: Enable write operations with `--edit-mode` flag
- ✅ **Strict validation**: Multiple security layers for both read and write operations
- ✅ **Connection string by parameter**: Passed when starting the server
- ✅ **Transaction support**: Write operations use transactions for data integrity
- ✅ **Versioning support**: Track changes and updates

### Available Tools

#### Read-only tools (always available):
- `execute_query`: Executes SQL SELECT queries
- `list_tables`: Lists all database tables
- `describe_table`: Describes the structure of a table
- `get_version`: Gets current version and changelog information

#### Write tools (only available with `--edit-mode`):
- `execute_write_query`: Executes write SQL queries (INSERT, UPDATE, DELETE, DDL)
- `create_table`: Creates new tables with specified columns
- `drop_table`: Drops existing tables
- `insert_data`: Inserts new records into tables
- `update_data`: Updates existing records in tables
- `delete_data`: Deletes records from tables

## Usage

### Command Line

#### Read-only mode (default)
```bash
node dist/index.js "Server=localhost;Database=mydb;User Id=user;Password=pass;"
```

#### Edit mode (write operations enabled)
```bash
node dist/index.js --edit-mode "Server=localhost;Database=mydb;User Id=user;Password=pass;"
```

### Claude Desktop Configuration

Configure the server in your Claude Desktop settings by adding the `--edit-mode` flag to the `args` array when you need write operations enabled. See the [Claude Desktop Configuration Examples](#claude-desktop-configuration-examples) section below for detailed examples.

## Implemented Security

### Read-only Mode (Default)

#### ✅ **Allowed:**
- Simple and complex `SELECT` queries
- `JOIN`, `GROUP BY`, `ORDER BY`, `HAVING`
- Subqueries and CTEs (SELECT only)
- Aggregate functions (`COUNT`, `SUM`, `AVG`, etc.)

#### ❌ **Blocked:**
- **Write operations**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`
- **Multiple statements**: Queries separated by `;`
- **System functions**: `xp_cmdshell`, `sp_configure`, `OPENROWSET`, etc.
- **Comments**: `--` and `/* */` for security
- **Variables**: `DECLARE`, `SET` to prevent injection
- **Procedures**: `EXEC`, `sp_executesql`
- **Malicious CTEs**: Common Table Expressions with write operations

### Edit Mode (--edit-mode flag)

#### ✅ **Allowed:**
- All read-only operations listed above
- **Write operations**: `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `DROP`, `TRUNCATE`
- **Structured operations**: via dedicated tools (create_table, insert_data, etc.)
- **Transaction support**: Automatic rollback on errors

#### ❌ **Still Blocked:**
- **Multiple statements**: Queries separated by `;`
- **Dangerous system functions**: `xp_cmdshell`, `sp_configure`, `OPENROWSET`, etc.
- **Comments**: `--` and `/* */` for security
- **Bulk operations**: `BULK INSERT`, `OPENROWSET`

See `SECURITY_TESTS.md` for detailed examples.

## Installation

```bash
cd sqlserver
npm install
npm run build
```

## Available Tools

### Read-only tools (always available):
- **execute_query**: Executes SQL SELECT queries
- **list_tables**: Lists all database tables  
- **describe_table**: Describes the structure of a specific table
- **get_version**: Gets current version and changelog information

### Write tools (only available with `--edit-mode` flag):
- **execute_write_query**: Executes write SQL queries (INSERT, UPDATE, DELETE, DDL)
- **create_table**: Creates new tables with specified columns
- **drop_table**: Drops existing tables
- **insert_data**: Inserts new records into tables
- **update_data**: Updates existing records in tables
- **delete_data**: Deletes records from tables

## Connection String Format

```
Server=server;Database=database;User Id=username;Password=password;Encrypt=true;TrustServerCertificate=true;
```

## Claude Desktop Configuration Examples

Add this to your Claude Desktop configuration file:

### Read-only mode (default, secure)
```json
{
  "mcpServers": {
    "sqlserver": {
      "command": "node",
      "args": [
        "/path/to/your/project/sqlserver/dist/index.js",
        "Server=localhost;Database=mydb;User Id=user;Password=pass;Encrypt=true;TrustServerCertificate=true;"
      ]
    }
  }
}
```

### Edit mode (write operations enabled)
```json
{
  "mcpServers": {
    "sqlserver": {
      "command": "node",
      "args": [
        "/path/to/your/project/sqlserver/dist/index.js",
        "--edit-mode",
        "Server=localhost;Database=mydb;User Id=user;Password=pass;Encrypt=true;TrustServerCertificate=true;"
      ]
    }
  }
}
```

### Alternative edit mode configuration (using -e flag)
```json
{
  "mcpServers": {
    "sqlserver": {
      "command": "node",
      "args": [
        "/path/to/your/project/sqlserver/dist/index.js",
        "-e",
        "Server=localhost;Database=mydb;User Id=user;Password=pass;Encrypt=true;TrustServerCertificate=true;"
      ]
    }
  }
}
```

> **⚠️ Security Note**: Only use edit mode when you need write operations. Read-only mode is recommended for most use cases to prevent accidental data modifications.

## Version Management

### Checking Version

You can check the current version using the `get_version` tool, which provides:
- Current version number
- Server information
- Changelog for the current version

### Updating Version

Use the provided script to update versions:

```bash
# Increment patch version (1.0.0 -> 1.0.1)
./update-version.sh patch "Fixed SQL validation bug"

# Increment minor version (1.0.0 -> 1.1.0)
./update-version.sh minor "Added new query feature"

# Increment major version (1.0.0 -> 2.0.0)
./update-version.sh major "Breaking API changes"
```

The script automatically:
- Updates VERSION file
- Updates package.json
- Adds entry to CHANGELOG.md
- Shows next steps for git tagging

### Version History

All changes are documented in [CHANGELOG.md](CHANGELOG.md) following the [Keep a Changelog](https://keepachangelog.com/) format.