# MCP Services Collection

This collection contains multiple MCP (Model Context Protocol) servers for different services.

## Available Services

### 🗃️ SQL Server (`sqlserver/`)
Python-based MCP server for performing read-only and configurable write operations on SQL Server databases.

- **Features**: Read-only by default, configurable edit mode, strict security validation, automatic serialization
- **Tools**: `execute_query`, `list_tables`, `describe_table`, `show_version`, and write tools in edit mode
- **Implementation**: Python with pyodbc
- **Documentation**: [sqlserver/README.md](sqlserver/README.md)

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

# Test the server
python server.py --help
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