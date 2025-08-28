# On-Call Rotation MCP Server

Python MCP server that answers: "Who is on duty on a given date?" It uses a cyclic engineer rotation with optional overrides.

## Configuration

Configuration is supplied via either the environment variable `MCP_ROTATION_CONFIG` (JSON string) or an adjacent `config.json` file. Environment variable takes precedence.

### JSON Schema (conceptual)
```
{
  "engineers": [ "Alice", "Bob", "Carol" ],          // Required. Ordered list, first engineer starts at start_date.
  "start_date": "2025-08-25",                           // Required. ISO date (YYYY-MM-DD). Baseline cycle start.
  "rotation_days": 7,                                    // Optional. Integer > 0. Length (in days) of each slot. Default 7.
  "overrides": [                                         // Optional. Persistent overrides (JSON, internal storage only)
    { "date": "2025-09-10", "engineer": "David" }
  ]                                                        // NOTE: Ad‑hoc overrides via the tool now use a string format.
}
```

### Override Semantics
For any target date the server:
1. Collects all overrides (persistent + ad‑hoc passed to the tool) whose `date` ≤ target date.
2. Selects the override with the latest `date` (most recent past).
3. If the selected override spans across a regular rotation boundary, it still applies until (a) another override begins or (b) the next regular schedule change AFTER the override start (whichever comes first). This keeps overrides focused while preserving predictable cadence.

### Ad‑hoc Overrides (Tool Parameter) - NEW FORMAT
The `get_oncall` tool now accepts an `overrides` string in a compact pair format:

```
"Engineer One:2025-09-01,Engineer Two:2025-10-12"
```

Rules:
1. Pairs separated by commas.
2. Each pair = engineer name, a colon, an ISO date (YYYY-MM-DD).
3. Whitespace around names/dates is trimmed.
4. Duplicate (date+engineer) pairs are ignored after the first occurrence.
5. Invalid pairs (missing colon / bad date) return an error.

Semantics remain the same: an override becomes active at 00:00 of its date and remains until the next schedule boundary or a later override date, whichever comes first.

### Edge Cases & Validation
* Empty `engineers` → error.
* Invalid date format → error.
* `rotation_days` missing or ≤ 0 → defaults to 7.
* Dates before `start_date` are supported (rotation cycles backwards deterministically).

## Tools

| Tool | Description |
|------|-------------|
| `get_oncall` | Returns engineer on duty for a target date applying rotation + overrides. |
| `show_version` | Returns version plus parsed changelog entries. |

### `get_oncall` Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `date` | `str` | Yes | Target date (YYYY-MM-DD). |
| `overrides` | `str` | No | Compact overrides string: `Name:YYYY-MM-DD[,Name2:YYYY-MM-DD...]`. |

### `get_oncall` Response (JSON string)
```
{
  "date": "2025-09-18",
  "engineer": "Alice",
  "source": "schedule" | "override",
  "rotation_start": "2025-08-25",
  "rotation_days": 7,
  "slot_index": 3,           // Zero-based slot index since start_date
  "engineer_index": 0,       // Index in engineers array after modulo
  "total_engineers": 3,
  "applied_override": {      // Present only if source=override
    "date": "2025-09-17",
    "engineer": "Bob"
  }
}
```

## Versioning & Changelog
* `VERSION` contains semantic version (e.g. `0.1.0`).
* `CHANGELOG.md` follows Keep a Changelog style headings and is parsed by `show_version`.

## Local Development
```bash
cd mcp-services/oncall-rotation
pip install -r requirements.txt
python -m pytest -v
python server.py  # Runs MCP server
```

## Example Usage (Environment Config)
```bash
export MCP_ROTATION_CONFIG='{"engineers":["Alice","Bob"],"start_date":"2025-08-25","rotation_days":7}'
python server.py
```

## License
Same license as repository.
