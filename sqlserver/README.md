# MCP SQL Server Server

A simple MCP (Model Context Protocol) server for performing read-only queries on SQL Server databases.

## Features

- ✅ **Read-only**: Only allows `SELECT` queries
- ✅ **Strict validation**: Multiple security layers
- ✅ **Connection string by parameter**: Passed when starting the server
- ✅ **Three available tools**:
  - `execute_query`: Executes SQL SELECT queries
  - `list_tables`: Lists all database tables
  - `describe_table`: Describes the structure of a table

## Implemented Security

### ✅ **Allowed:**
- Simple and complex `SELECT` queries
- `JOIN`, `GROUP BY`, `ORDER BY`, `HAVING`
- Subqueries and CTEs (SELECT only)
- Aggregate functions (`COUNT`, `SUM`, `AVG`, etc.)

### ❌ **Blocked:**
- **Write operations**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`
- **Multiple statements**: Queries separated by `;`
- **System functions**: `xp_cmdshell`, `sp_configure`, `OPENROWSET`, etc.
- **Comments**: `--` and `/* */` for security
- **Variables**: `DECLARE`, `SET` to prevent injection
- **Procedures**: `EXEC`, `sp_executesql`
- **Malicious CTEs**: Common Table Expressions with write operations

See `SECURITY_TESTS.md` for detailed examples.

## Installation

```bash
cd sqlserver
npm install
npm run build
```

## Available Tools

1. **execute_query**: Executes SELECT queries
2. **list_tables**: Lists all database tables
3. **describe_table**: Describes the structure of a specific table

## Connection String Format

```
Server=server;Database=database;User Id=username;Password=password;Encrypt=true;TrustServerCertificate=true;
```

## Claude Desktop Configuration Example

Add this to your Claude Desktop configuration file:

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