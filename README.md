# MCP Services Collection

This collection contains multiple MCP (Model Context Protocol) servers for different services.

## Available Services

### 🗃️ SQL Server (`sqlserver/`)
MCP server for performing read-only queries on SQL Server databases.

- **Features**: Read-only access, strict security validation, version management
- **Tools**: `execute_query`, `list_tables`, `describe_table`, `get_version`
- **Version**: 1.0.0
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

# Build a specific service
cd sqlserver
npm install
npm run build
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
├── sqlserver/               # MCP Server for SQL Server
│   ├── README.md
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   └── index.ts
│   ├── SECURITY_TESTS.md
│   ├── test-server.sh
│   └── mcp-config-example.json
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
- `package.json` - Dependencies and scripts
- `src/` - MCP server source code
- `mcp-config-example.json` - Configuration example for Claude Desktop

## Contributing

To contribute new services or improvements:

1. Fork this repository
2. Create a branch for your service/improvement
3. Add your service in a separate folder
4. Update documentation
5. Submit a Pull Request