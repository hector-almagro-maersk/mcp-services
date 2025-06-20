# MCP Services Collection

This collection contains multiple MCP (Model Context Protocol) servers for different services.

## Available Services

### 🗃️ SQL Server (`sqlserver/`)
MCP server for performing read-only queries on SQL Server databases.

- **Features**: Read-only access, strict security validation
- **Tools**: `execute_query`, `list_tables`, `describe_table`
- **Documentation**: [sqlserver/README.md](sqlserver/README.md)

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