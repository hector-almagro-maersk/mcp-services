# MCP SQL Server Database Connector

This server provides a Model Context Protocol (MCP) interface to a Microsoft SQL Server database, enabling secure, structured, and extensible access to database metadata and data via a set of well-defined tools. It is designed to be used as a backend for MCP clients, such as VS Code extensions, automation agents, or other MCP-compatible tools.

## Features

- **Read-only and write (edit mode) access** to SQL Server databases via MCP tools
- **Strict security validation** for all SQL queries (prevents SQL injection, only allows safe operations)
- **Automatic serialization** of date, time, and decimal types
- **Table and schema introspection**
- **Configurable via environment variables and command-line flags**

## How to Use

### 1. Add to MCP Configuration

In your VS Code `settings.json` (or other MCP-compatible configuration), add a server entry like:

```jsonc
"mcp": {
  "servers": {
    "pythonSqlServerMcp": {
      "command": "/path/to/python",
      "args": [
        "/path/to/python-sqlserver/server.py"
      ],
      "env": {
        "MCP_SQLSERVER_CONNECTION_STRING": "DRIVER={ODBC Driver 17 for SQL Server};Server=...;DATABASE=...;UID=...;PWD=...;..."
      }
    }
  }
}
```

- `command`: Path to your Python interpreter (ideally a virtual environment with dependencies installed)
- `args`: Path to `server.py` (this file)
- `env.MCP_SQLSERVER_CONNECTION_STRING`: The full ODBC connection string for your SQL Server instance

#### Optional: Enable Edit Mode
- Add `-e` or `--edit-mode` to the `args` array, or set the environment variable `MCP_SQLSERVER_EDIT_MODE=1` to enable write operations (INSERT, UPDATE, DELETE, DDL).

### 2. Install Dependencies

Install Python dependencies in your environment:

```sh
pip install pyodbc
```

## Tools Provided

### Read-Only Tools (Always Enabled)

- **show_version**: Returns the current version and changelog as JSON
- **list_tables**: Lists all tables in the database
- **describe_table(table_name)**: Describes the columns and types of a table
- **execute_query(query)**: Executes a read-only SQL SELECT query (with strict validation)

### Write Tools (Edit Mode Only)

- **execute_write_query(query)**: Executes a write SQL query (INSERT, UPDATE, DELETE, DDL)
- **create_table(table_name, columns)**: Creates a new table
- **drop_table(table_name)**: Drops a table
- **insert_data(table_name, data)**: Inserts a row into a table
- **update_data(table_name, data, where_clause)**: Updates rows in a table
- **delete_data(table_name, where_clause)**: Deletes rows from a table

> **Security:** All queries are strictly validated. Only safe operations are allowed. No multiple statements, comments, or dangerous keywords.

## Environment Variables

- `MCP_SQLSERVER_CONNECTION_STRING` (**required**): The ODBC connection string for your SQL Server.
- `MCP_SQLSERVER_EDIT_MODE` (optional): Set to `1`, `true`, `yes`, or `on` to enable write tools.

## Command-Line Flags

- `-e` or `--edit-mode`: Enable edit mode (write tools)

## Example Configuration (settings.json)

```jsonc
"mcp": {
  "servers": {
    "pythonSqlServerMcp": {
      "command": "/Users/youruser/Documents/GitHub Private/mcp-services/.venv/bin/python",
      "args": [
        "/Users/youruser/Documents/GitHub Private/mcp-services/python-sqlserver/server.py",
        "-e"
      ],
      "env": {
        "MCP_SQLSERVER_CONNECTION_STRING": "DRIVER={ODBC Driver 17 for SQL Server};Server=...;DATABASE=...;UID=...;PWD=...;..."
      }
    }
  }
}
```

## Security Notes

- Only SELECT queries are allowed in read-only mode.
- Write operations are only available in edit mode and are still strictly validated.
- No multiple SQL statements, comments, or forbidden keywords are allowed in any query.

## Versioning and Changelog

- The server reads its version from the `VERSION` file and changelog from `../sqlserver/CHANGELOG.md`.

## Extending

- You can add new MCP tools by defining new `@mcp.tool`-decorated functions in `server.py`.

## License

See repository for license details.
