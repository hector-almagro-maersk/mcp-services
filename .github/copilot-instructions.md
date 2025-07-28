# Copilot Instructions for MCP Services Repository

This guide enables AI coding agents to be productive in the `mcp-services` monorepo, which contains multiple Python-based Model Context Protocol (MCP) servers for different services. Follow these conventions and workflows for effective contributions and automation.

## Architecture Overview
- **Monorepo Structure:** Each service (e.g., `sqlserver`, `kubernetes`, `azure-storage`, `spotify-tools`) is in its own folder with a consistent layout: `README.md`, `requirements.txt`, `server.py`, `VERSION`, `CHANGELOG.md`, and tests.
- **Service Boundaries:** Each folder is a standalone MCP server, exposing tools via Python functions. No cross-service imports; communication is via MCP protocol only.
- **Data Flow:** All servers are stateless, operate via request/response, and use environment variables or config files for secrets and connection info.
- **Why:** This structure enables isolated development, easy CI/CD, and clear service ownership.

## Developer Workflows
- **Setup:**
  - Clone repo, then for each service: `pip install -r requirements.txt`.
  - Validate with `python -m py_compile server.py`.
- **Testing:**
  - Run tests with `python -m pytest test_server.py` (or `test_server_tools.py` for tool-level tests).
- **Builds:**
  - Use GitHub Actions workflow "Build MCP Server" for automated builds and artifact generation. See `.github/workflows/README.md`.
- **Configuration:**
  - Secrets and connection info via environment variables (preferred) or `config.json`.
  - Example: `MCP_SQLSERVER_CONNECTION_STRING`, `MCP_AZURE_STORAGE_CONFIG`, `MCP_SPOTIFY_CLIENT_ID`.

## Project-Specific Patterns
- **Tool Exposure:** All MCP tools are Python functions, typically decorated (e.g., `@mcp.tool`). See each `server.py` for available tools and their parameters.
- **Security:** Strict validation for all external connections and queries. SQL Server only allows safe queries; Azure/Spotify credentials are never logged.
- **Versioning:** Each service reads its version from `VERSION` and changelog from `CHANGELOG.md`.
- **Extensibility:** Add new tools by defining new functions in `server.py` and documenting them in the service's `README.md`.

## Integration Points
- **External Dependencies:**
  - SQL Server: `pyodbc`
  - Kubernetes: `kubernetes` Python client, Azure CLI for AKS
  - Azure Storage: `azure-storage-blob`, `azure-core`
  - Spotify: `spotipy` or direct API calls
- **MCP Client Integration:** Configure each server in your MCP client (e.g., VS Code) with the correct command, args, and env vars.

## Examples
- **SQL Server MCP:**
  - Read-only by default; enable edit mode via `-e` flag or env var.
  - Tools: `list_tables`, `describe_table`, `execute_query`, `show_version`.
- **Kubernetes MCP:**
  - Tools: `list_pods`, `get_pod_details`, `get_pod_logs`, `azure_login`, `restart_pod`.
- **Azure Storage MCP:**
  - Tools: `list_containers`, `check_containers`, `list_blobs`, `show_version`.
- **Spotify Tools MCP:**
  - Tools: `search_spotify`, `get_track_info`, `get_album_info`, `get_artist_info`, `show_version`.

## Conventions
- **No cross-service imports.**
- **All secrets/configs via env vars or config files.**
- **Document new tools and changes in `README.md` and `CHANGELOG.md`.**
- **Tests must be in the same folder as the service.**

## Key Files
- `README.md` (root): Big-picture architecture, quick start, build/test instructions.
- `[service]/README.md`: Service-specific usage, configuration, and tool documentation.
- `.github/workflows/README.md`: CI/CD workflow details.

---

For unclear or missing conventions, review the relevant `README.md` or ask for clarification. Update this file as new services or patterns are added.
