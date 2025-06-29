from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MCP SQL Server Database Connector")

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
        import os
        import pyodbc
        conn_str = os.environ.get("MCP_SQLSERVER_CONNECTION_STRING")
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
        import os
        import pyodbc
        conn_str = os.environ.get("MCP_SQLSERVER_CONNECTION_STRING")
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

if __name__ == "__main__":
    mcp.run()
