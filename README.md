# MCP Services Collection

This collection contains multiple MCP (Model Context Protocol) servers for different services.

## Available Services

### 🗃️ SQL Server (`sqlserver/`)
Python-based MCP server for performing read-only and configurable write operations on SQL Server databases.

- **Features**: Read-only by default, configurable edit mode, strict security validation, automatic serialization
- **Tools**: `execute_query`, `list_tables`, `describe_table`, `show_version`, and write tools in edit mode
- **Implementation**: Python with pyodbc
- **Documentation**: [sqlserver/README.md](sqlserver/README.md)

### ☸️ Kubernetes (`kubernetes/`)
Python-based MCP server for monitoring and interacting with Kubernetes clusters.

- **Features**: Pod management, health monitoring, restart tracking, log retrieval, namespace management, Azure AD authentication
- **Tools**: `list_pods`, `list_non_running_pods`, `list_restarted_pods`, `get_pod_details`, `get_pod_logs`, `list_namespaces`, `get_cluster_health`, `azure_login`, `azure_status`, `restart_pod`, `show_version`
- **Implementation**: Python with kubernetes client library and Azure CLI integration
- **Documentation**: [kubernetes/README.md](kubernetes/README.md)

### ☁️ Azure Storage (`azure-storage/`)
Python-based MCP server for monitoring Azure Blob Storage containers.

- **Features**: Container monitoring, blob listing, flexible authentication, detailed reporting, secure configuration
- **Tools**: `list_containers`, `check_containers`, `check_container`, `list_blobs`, `show_version`
- **Implementation**: Python with azure-storage-blob SDK
- **Documentation**: [azure-storage/README.md](azure-storage/README.md)

### 📟 On-Call Rotation (`oncall-rotation/`)
Python-based MCP server to compute the engineer on duty for any date using a cyclic rotation plus optional overrides.

- **Features**: Deterministic rotation, ad-hoc & persistent overrides, negative date support, changelog reporting
- **Tools**: `get_oncall`, `show_version`
- **Implementation**: Pure Python (no external date libs) using `datetime`
- **Documentation**: [oncall-rotation/README.md](oncall-rotation/README.md)

### 🎵 Spotify Tools (`spotify-tools/`)
Python-based MCP server for comprehensive read-only access to Spotify music metadata and discovery features.

- **Features**: Unified search, track/album/artist/playlist detail retrieval, recommendations, browse (new releases, featured playlists, categories), audio features & analysis, market-specific queries
- **Tools**: `search_spotify`, `get_track_info`, `get_album_info`, `get_artist_info`, `get_playlist_info`, `get_recommendations`, `get_new_releases`, `get_featured_playlists`, `get_browse_categories`, `show_version` (and additional specialized tools)
- **Implementation**: Python using Spotify Web API via `requests`
- **Documentation**: [spotify-tools/README.md](spotify-tools/README.md)

## 🚀 Quick Start

### Download Pre-built Artifacts
1. Go to the **Actions** tab in this repository
2. Run the "Build MCP Server" workflow
3. Select your desired MCP service from the dropdown
4. Download the generated artifact
5. Extract and use the compiled MCP server

### Local Development
```bash
# Clone the repository
git clone https://github.com/hector-almagro-maersk/mcp-services.git
cd mcp-services

# Set up Python environment for sqlserver
cd sqlserver
pip install -r requirements.txt

# Validate the server
python -m py_compile server.py

# Or set up Python environment for kubernetes
cd ../kubernetes
pip install -r requirements.txt

# Validate the server
python -m py_compile server.py

# Or set up Python environment for azure-storage
cd ../azure-storage
pip install -r requirements.txt

# Validate the server
python -m py_compile server.py

# Or set up Python environment for oncall-rotation
cd ../oncall-rotation
pip install -r requirements.txt

# Validate the server
python -m py_compile server.py

# Or set up Python environment for spotify-tools
cd ../spotify-tools
pip install -r requirements.txt

# Validate the server
python -m py_compile server.py
```

## 🏗️ Automated Builds

This repository includes a GitHub Actions workflow for automated building:

### 🎯 Build Individual MCP Server
- **Workflow**: Build MCP Server
- **Trigger**: Manual dispatch with service selection
- **Features**: Dropdown selection, version detection, artifact generation

**Artifact Details:**
- **Naming**: `{service-name}-v{version}`
- **Contents**: Compiled code, documentation, configuration files
- **Retention**: 90 days
- **Overwrite**: Same versions are overwritten automatically

See [.github/workflows/README.md](.github/workflows/README.md) for detailed workflow documentation.

## Repository Structure

```
mcp-services/
├── README.md                 # This file
├── sqlserver/               # Python MCP Server for SQL Server
│   ├── README.md
│   ├── requirements.txt
│   ├── server.py
│   ├── CHANGELOG.md
│   ├── VERSION
│   ├── test_server.py
│   └── test_server_tools.py
├── kubernetes/              # Python MCP Server for Kubernetes
│   ├── README.md
│   ├── requirements.txt
│   ├── server.py
│   ├── CHANGELOG.md
│   ├── VERSION
│   ├── test_server.py
│   └── test_server_tools.py
├── azure-storage/           # Python MCP Server for Azure Blob Storage
│   ├── README.md
│   ├── requirements.txt
│   ├── server.py
│   ├── CHANGELOG.md
│   ├── VERSION
│   ├── test_server.py
│   └── config.json
├── oncall-rotation/         # Python MCP Server for on-call engineer rotation
│   ├── README.md
│   ├── requirements.txt
│   ├── server.py
│   ├── CHANGELOG.md
│   ├── VERSION
│   └── test_server.py
├── spotify-tools/           # Python MCP Server for Spotify metadata & discovery
│   ├── README.md
│   ├── requirements.txt
│   ├── server.py
│   ├── CHANGELOG.md
│   └── VERSION
└── [other-services]/       # Future MCP services
```

## Adding New Services

To add a new MCP service:

1. Create a new folder with the service name
2. Include all necessary service files
3. Add service-specific documentation
4. Update this README with the new information

## General Configuration

Each service includes:
- `README.md` - Service-specific documentation
- `requirements.txt` - Python dependencies (for Python services)
- `server.py` - MCP server implementation (for Python services)
- Configuration examples and documentation

## Contributing

To contribute new services or improvements:

1. Fork this repository
2. Create a branch for your service/improvement
3. Add your service in a separate folder
4. Update documentation
5. Submit a Pull Request