import re
from mcp.server.fastmcp import FastMCP
import sys

mcp = FastMCP("MCP SQL Server Database Connector")

def get_connection_string() -> str:
    """Retrieve the SQL Server connection string from the environment variable."""
    import os
    return os.environ.get("MCP_SQLSERVER_CONNECTION_STRING")

@mcp.tool(description="Show the current MCP version and the full changelog as structured JSON.")
def show_version() -> str:
    """Return the MCP version and the full changelog as JSON: [{version, date, changes: {type: [list]}}]."""
    try:
        import os
        import re
        import json
        version_path = os.path.join(os.path.dirname(__file__), "VERSION")
        changelog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sqlserver", "CHANGELOG.md")
        # Read version
        with open(version_path, "r") as f:
            version = f.read().strip()
        changelog_entries = []
        if os.path.exists(changelog_path):
            with open(changelog_path, "r") as f:
                changelog = f.read()
            # Find all version headings
            version_pattern = re.compile(r"^##+\s*\[?v?(\d+\.\d+\.\d+(?:-[^\]\s]+)?)\]?\s*-?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})?\s*$", re.MULTILINE)
            matches = list(version_pattern.finditer(changelog))
            for i, m in enumerate(matches):
                v = m.group(1)
                date = m.group(2) or None
                start = m.end()
                end = matches[i+1].start() if i+1 < len(matches) else len(changelog)
                section = changelog[start:end].strip()
                # Find all change types and their lists
                changes = {}
                # Change type headings: ### Added, ### Changed, etc.
                type_pattern = re.compile(r"^###\s+([A-Za-z ]+)\s*$", re.MULTILINE)
                type_matches = list(type_pattern.finditer(section))
                for j, t in enumerate(type_matches):
                    change_type = t.group(1).strip()
                    t_start = t.end()
                    t_end = type_matches[j+1].start() if j+1 < len(type_matches) else len(section)
                    # Extract bullet points
                    bullets = re.findall(r"^[-*]\s+(.*)$", section[t_start:t_end], re.MULTILINE)
                    changes[change_type] = bullets
                changelog_entries.append({
                    "version": v,
                    "date": date,
                    "changes": changes
                })
        result = {
            "current_version": version,
            "changelog": changelog_entries
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error reading version or changelog: {e}"})

@mcp.tool(description="List all tables in the SQL Server database defined by the MCP_SQLSERVER_CONNECTION_STRING environment variable.")
def list_tables() -> str:
    """
    List all tables in the SQL Server database.
    The connection string must be provided via the MCP_SQLSERVER_CONNECTION_STRING environment variable.
    """
    try:
        import pyodbc
        conn_str = get_connection_string()
        if not conn_str:
            return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
        with pyodbc.connect(conn_str, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            rows = cursor.fetchall()
            # Match the output format of index.ts: JSON array of dicts
            columns = [column[0] for column in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
            import json
            return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error listing tables: {e}"

@mcp.tool(description="Describe the structure of a specific table in the SQL Server database. The connection string must be provided via the MCP_SQLSERVER_CONNECTION_STRING environment variable.")
def describe_table(table_name: str) -> str:
    """
    Describe the structure of a specific table in the SQL Server database.
    The connection string must be provided via the MCP_SQLSERVER_CONNECTION_STRING environment variable.
    """
    try:
        import pyodbc
        conn_str = get_connection_string()
        if not conn_str:
            return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
        with pyodbc.connect(conn_str, timeout=10) as conn:
            cursor = conn.cursor()
            # Parse schema and table name
            schema_name = 'dbo'
            actual_table_name = table_name
            if '.' in table_name:
                parts = table_name.split('.')
                if len(parts) == 2:
                    schema_name, actual_table_name = parts
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, (schema_name, actual_table_name))
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
            import json
            return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error describing table: {e}"

def is_edit_mode() -> bool:
    """Determine if edit mode is enabled via environment variable or command-line flag."""
    import os
    # Check environment variable first
    if os.environ.get("MCP_SQLSERVER_EDIT_MODE", "").lower() in ("1", "true", "yes", "on"): 
        return True
    # Check command-line flag
    return any(arg in ("--edit-mode", "-e") for arg in sys.argv)

@mcp.tool(description="Executes a read-only SQL query (SELECT) on the SQL Server database.")
def execute_query(query: str) -> str:
    """Executes a read-only SQL query (SELECT) with strict validation and serializes datetimes as ISO strings."""
    try:
        import pyodbc, re, json, datetime, decimal
        conn_str = get_connection_string()
        if not conn_str:
            return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
        # Security: Only allow SELECT, no comments, no multiple statements, no forbidden keywords
        q = query.strip()
        if not q.lower().startswith("select"):
            return "Only SELECT queries are allowed."
        if ";" in q:
            return "Multiple SQL statements are not allowed."
        if re.search(r"(--|/\*)", q):
            return "Comments are not allowed in queries."
        forbidden = [
            'insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate',
            'exec', 'execute', 'sp_', 'xp_', 'merge', 'bulk', 'openrowset',
            'opendatasource', 'openquery', 'openxml', 'writetext', 'updatetext',
            'backup', 'restore', 'dbcc', 'shutdown', 'reconfigure', 'grant',
            'revoke', 'deny', 'use ', 'go ', 'declare', 'set ', 'print'
        ]
        for word in forbidden:
            if re.search(rf"\\b{re.escape(word)}\\b", q, re.IGNORECASE):
                return f"Forbidden keyword detected: {word}"
        with pyodbc.connect(conn_str, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute(q)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            def to_serializable(val):
                if isinstance(val, (datetime.datetime, datetime.date)):
                    return val.isoformat()
                if isinstance(val, decimal.Decimal):
                    return float(val)
                return val
            result = [dict(zip(columns, [to_serializable(v) for v in row])) for row in rows]
            return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing query: {e}"

# Write endpoints (only enabled in edit mode)
if is_edit_mode():
    @mcp.tool(description="Executes a write SQL query (INSERT, UPDATE, DELETE, DDL) on the SQL Server database. Edit mode only.")
    def execute_write_query(query: str) -> str:
        """Executes a write SQL query (INSERT, UPDATE, DELETE, DDL) with strict validation and transaction."""
        try:
            import pyodbc, re
            conn_str = get_connection_string()
            if not conn_str:
                return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
            q = query.strip()
            allowed = ["insert", "update", "delete", "create", "alter", "drop", "truncate"]
            if not any(q.lower().startswith(cmd) for cmd in allowed):
                return "Query must be a valid write operation (INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, TRUNCATE)"
            if ";" in q:
                return "Multiple SQL statements are not allowed."
            if re.search(r"(--|/\*)", q):
                return "Comments are not allowed in queries."
            forbidden = [
                'xp_cmdshell', 'sp_configure', 'openrowset', 'opendatasource',
                'fn_get_audit_file', 'bulk', 'sp_executesql'
            ]
            for word in forbidden:
                if re.search(rf"\\b{re.escape(word)}\\b", q, re.IGNORECASE):
                    return f"Forbidden keyword detected: {word}"
            with pyodbc.connect(conn_str, timeout=10, autocommit=False) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(q)
                    affected = cursor.rowcount
                    conn.commit()
                    return f"Write query executed successfully. Rows affected: {affected}"
                except Exception as e:
                    conn.rollback()
                    return f"Error executing write query: {e}"
        except Exception as e:
            return f"Error executing write query: {e}"

    @mcp.tool(description="Create a new table. Edit mode only.")
    def create_table(table_name: str, columns: list) -> str:
        """Create a new table with the given columns (list of dicts: name, type, nullable, default)."""
        try:
            import pyodbc
            conn_str = get_connection_string()
            if not conn_str:
                return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
            # Validate table name
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", table_name):
                return "Invalid table name."
            # Build column definitions
            col_defs = []
            for col in columns:
                col_str = f"[{col['name']}] {col['type']}"
                if not col.get('nullable', True):
                    col_str += " NOT NULL"
                if col.get('default') is not None:
                    col_str += f" DEFAULT {col['default']}"
                col_defs.append(col_str)
            table = ".".join(f"[{p}]" for p in table_name.split("."))
            sql = f"CREATE TABLE {table} ({', '.join(col_defs)})"
            with pyodbc.connect(conn_str, timeout=10, autocommit=False) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(sql)
                    conn.commit()
                    return f"Table {table_name} created successfully."
                except Exception as e:
                    conn.rollback()
                    return f"Error creating table: {e}"
        except Exception as e:
            return f"Error creating table: {e}"

    @mcp.tool(description="Drop a table. Edit mode only.")
    def drop_table(table_name: str) -> str:
        """Drop a table by name."""
        try:
            import pyodbc, re
            conn_str = get_connection_string()
            if not conn_str:
                return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", table_name):
                return "Invalid table name."
            table = ".".join(f"[{p}]" for p in table_name.split("."))
            sql = f"DROP TABLE {table}"
            with pyodbc.connect(conn_str, timeout=10, autocommit=False) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(sql)
                    conn.commit()
                    return f"Table {table_name} dropped successfully."
                except Exception as e:
                    conn.rollback()
                    return f"Error dropping table: {e}"
        except Exception as e:
            return f"Error dropping table: {e}"

    @mcp.tool(description="Insert data into a table. Edit mode only.")
    def insert_data(table_name: str, data: dict) -> str:
        """Insert a row into a table. Data is a dict of column:value."""
        try:
            import pyodbc, re
            conn_str = get_connection_string()
            if not conn_str:
                return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", table_name):
                return "Invalid table name."
            columns = list(data.keys())
            values = list(data.values())
            col_str = ", ".join(f"[{c}]" for c in columns)
            param_str = ", ".join(["?" for _ in columns])
            table = ".".join(f"[{p}]" for p in table_name.split("."))
            sql = f"INSERT INTO {table} ({col_str}) VALUES ({param_str})"
            with pyodbc.connect(conn_str, timeout=10, autocommit=False) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(sql, values)
                    conn.commit()
                    return f"Row inserted into {table_name}."
                except Exception as e:
                    conn.rollback()
                    return f"Error inserting data: {e}"
        except Exception as e:
            return f"Error inserting data: {e}"

    @mcp.tool(description="Update data in a table. Edit mode only.")
    def update_data(table_name: str, data: dict, where_clause: str) -> str:
        """Update rows in a table. Data is a dict of column:value. where_clause is a SQL WHERE clause (without 'WHERE')."""
        try:
            import pyodbc, re
            conn_str = get_connection_string()
            if not conn_str:
                return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", table_name):
                return "Invalid table name."
            columns = list(data.keys())
            values = list(data.values())
            set_str = ", ".join(f"[{c}] = ?" for c in columns)
            table = ".".join(f"[{p}]" for p in table_name.split("."))
            sql = f"UPDATE {table} SET {set_str} WHERE {where_clause}"
            with pyodbc.connect(conn_str, timeout=10, autocommit=False) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(sql, values)
                    conn.commit()
                    return f"Rows updated in {table_name}."
                except Exception as e:
                    conn.rollback()
                    return f"Error updating data: {e}"
        except Exception as e:
            return f"Error updating data: {e}"

    @mcp.tool(description="Delete data from a table. Edit mode only.")
    def delete_data(table_name: str, where_clause: str) -> str:
        """Delete rows from a table. where_clause is a SQL WHERE clause (without 'WHERE')."""
        try:
            import pyodbc, re
            conn_str = get_connection_string()
            if not conn_str:
                return "No connection string provided. Set MCP_SQLSERVER_CONNECTION_STRING environment variable."
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", table_name):
                return "Invalid table name."
            table = ".".join(f"[{p}]" for p in table_name.split("."))
            sql = f"DELETE FROM {table} WHERE {where_clause}"
            with pyodbc.connect(conn_str, timeout=10, autocommit=False) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(sql)
                    conn.commit()
                    return f"Rows deleted from {table_name}."
                except Exception as e:
                    conn.rollback()
                    return f"Error deleting data: {e}"
        except Exception as e:
            return f"Error deleting data: {e}"

if __name__ == "__main__":
    mcp.run()
