import os
import tempfile
import datetime
import decimal
from server import (
    get_connection_string,
    read_file,
    parse_changelog,
    validate_table_name,
    validate_select_query,
    to_serializable
)

def test_get_connection_string(monkeypatch):
    monkeypatch.setenv("MCP_SQLSERVER_CONNECTION_STRING", "test_conn_str")
    assert get_connection_string() == "test_conn_str"

def test_read_file():
    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        f.write("hello world")
        fname = f.name
    try:
        assert read_file(fname) == "hello world"
    finally:
        os.remove(fname)

def test_parse_changelog():
    changelog = """
## [1.2.3] - 2024-01-01
### Added
- Feature A
- Feature B
### Fixed
- Bug X
## [1.2.2] - 2023-12-01
### Changed
- Something changed
"""
    entries = parse_changelog(changelog)
    assert len(entries) == 2
    assert entries[0]["version"] == "1.2.3"
    assert "Added" in entries[0]["changes"]
    assert entries[0]["changes"]["Added"] == ["Feature A", "Feature B"]
    assert entries[1]["version"] == "1.2.2"
    assert "Changed" in entries[1]["changes"]
    assert entries[1]["changes"]["Changed"] == ["Something changed"]

def test_validate_table_name():
    assert validate_table_name("MyTable")
    assert validate_table_name("schema.Table")
    assert not validate_table_name("1Table")
    assert not validate_table_name("bad-table")
    assert not validate_table_name("table;")

def test_validate_select_query():
    assert validate_select_query("SELECT * FROM foo") == ""
    assert "Only SELECT queries" in validate_select_query("UPDATE foo SET x=1")
    assert "Multiple SQL statements" in validate_select_query("SELECT * FROM foo; SELECT * FROM bar")
    assert "Comments are not allowed" in validate_select_query("SELECT * FROM foo -- comment")
    assert "Multiple SQL statements" in validate_select_query("SELECT * FROM foo; DROP TABLE bar")

def test_to_serializable():
    now = datetime.datetime(2024, 1, 1, 12, 0, 0)
    assert to_serializable(now) == now.isoformat()
    today = datetime.date(2024, 1, 1)
    assert to_serializable(today) == today.isoformat()
    dec = decimal.Decimal("1.23")
    assert to_serializable(dec) == float(dec)
    assert to_serializable("abc") == "abc"
