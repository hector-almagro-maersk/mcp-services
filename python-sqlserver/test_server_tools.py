from unittest.mock import patch, MagicMock
import server

def test_show_version(monkeypatch):
    # Patch read_file and parse_changelog
    monkeypatch.setattr(server, "read_file", lambda path: "1.0.0" if "VERSION" in path else "## [1.0.0] - 2024-01-01\n### Added\n- X")
    monkeypatch.setattr(server, "parse_changelog", lambda changelog: [{"version": "1.0.0", "date": "2024-01-01", "changes": {"Added": ["X"]}}])
    monkeypatch.setattr("os.path.exists", lambda path: True)
    result = server.show_version()
    assert 'current_version' in result
    assert 'changelog' in result

@patch("pyodbc.connect")
def test_list_tables(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("dbo", "Table1", "BASE TABLE")]
    mock_cursor.description = [("TABLE_SCHEMA",), ("TABLE_NAME",), ("TABLE_TYPE",)]
    mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
    with patch("server.get_connection_string", return_value="dummy"):
        result = server.list_tables()
        assert "Table1" in result

@patch("pyodbc.connect")
def test_describe_table(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("col1", "int", "NO", None, None, None, None)]
    mock_cursor.description = [("COLUMN_NAME",), ("DATA_TYPE",), ("IS_NULLABLE",), ("COLUMN_DEFAULT",), ("CHARACTER_MAXIMUM_LENGTH",), ("NUMERIC_PRECISION",), ("NUMERIC_SCALE",)]
    mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
    with patch("server.get_connection_string", return_value="dummy"):
        result = server.describe_table("dbo.Table1")
        assert "col1" in result

@patch("pyodbc.connect")
def test_execute_query(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [(1, "foo")]
    mock_cursor.description = [("id",), ("name",)]
    mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
    with patch("server.get_connection_string", return_value="dummy"):
        result = server.execute_query("SELECT * FROM foo")
        assert "foo" in result

# Write tools (edit mode only)
def enable_edit_mode(monkeypatch):
    monkeypatch.setenv("MCP_SQLSERVER_EDIT_MODE", "1")
    # Force reload to re-register tools
    import importlib
    importlib.reload(server)

@patch("pyodbc.connect")
def test_execute_write_query(mock_connect, monkeypatch):
    enable_edit_mode(monkeypatch)
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
    with patch("server.get_connection_string", return_value="dummy"):
        result = server.execute_write_query("insert into foo values (1)")
        assert "Rows affected" in result
