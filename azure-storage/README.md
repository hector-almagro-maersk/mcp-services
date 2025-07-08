# Azure Storage MCP Server

An MCP (Model Context Protocol) server for monitoring Azure Blob Storage containers. This server allows you to check if containers contain files and provides detailed information about blob storage resources.

## Features

- **Container Monitoring**: Check if configured containers contain any blobs
- **Flexible Authentication**: Support for both connection strings and account key authentication
- **Detailed Reporting**: Get comprehensive information about containers and their contents
- **Blob Listing**: List blobs in specific containers with optional filtering
- **Secure Configuration**: Secrets are not logged or exposed in responses

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your Azure Storage containers (see Configuration section below)

3. Run the server:
```bash
python server.py
```

## Configuration

The server supports two configuration methods:

### Method 1: Environment Variable (Recommended)

Set the `MCP_AZURE_STORAGE_CONFIG` environment variable with a JSON string:

```bash
export MCP_AZURE_STORAGE_CONFIG='{
  "containers": [
    {
      "container_name": "my-container-1",
      "account_name": "mystorageaccount",
      "account_key": "your-account-key"
    },
    {
      "container_name": "my-container-2",
      "connection_string": "DefaultEndpointsProtocol=https;AccountName=mystorageaccount;AccountKey=your-account-key;EndpointSuffix=core.windows.net"
    }
  ]
}'
```

### Method 2: Configuration File

Create a `config.json` file in the same directory as `server.py`:

```json
{
  "containers": [
    {
      "container_name": "my-container-1",
      "account_name": "mystorageaccount",
      "account_key": "your-account-key"
    },
    {
      "container_name": "my-container-2",
      "connection_string": "DefaultEndpointsProtocol=https;AccountName=mystorageaccount;AccountKey=your-account-key;EndpointSuffix=core.windows.net"
    }
  ]
}
```

### Authentication Options

Each container configuration supports two authentication methods:

1. **Connection String**: Use the `connection_string` field
2. **Account Name + Key**: Use both `account_name` and `account_key` fields

## MCP Integration

Add this server to your MCP client configuration (e.g., VS Code settings.json):

```json
{
  "mcp": {
    "servers": {
      "azureStorage": {
        "command": "/path/to/your/venv/bin/python",
        "args": ["/path/to/azure-storage/server.py"],
        "env": {
          "MCP_AZURE_STORAGE_CONFIG": "{\"containers\":[{\"container_name\":\"my-container\",\"account_name\":\"mystorageaccount\",\"account_key\":\"your-account-key\"}]}"
        }
      }
    }
  }
}
```

## Available Tools

### `list_containers`
Lists all configured Azure Blob Storage containers with their basic information.

### `check_containers`
Checks all configured containers to determine which ones contain blobs. Returns a summary with:
- Total number of containers
- Number of containers with blobs
- Number of empty containers
- Number of containers with errors
- Detailed results for each container

### `check_container(container_name)`
Checks a specific container to see if it contains blobs.

**Parameters:**
- `container_name`: The name of the container to check

### `list_blobs(container_name, max_results=10, prefix=None)`
Lists blobs in a specific container.

**Parameters:**
- `container_name`: The name of the container to list blobs from
- `max_results`: Maximum number of blobs to return (default: 10, max: 100)
- `prefix`: Optional prefix to filter blobs by name

### `show_version`
Shows the current server version and changelog.

## Example Usage

Once the server is running and configured in your MCP client, you can use these tools:

```
# List all configured containers
list_containers()

# Check which containers have files
check_containers()

# Check a specific container
check_container("my-important-container")

# List first 20 blobs in a container
list_blobs("my-container", 20)

# List blobs with a specific prefix
list_blobs("my-container", 10, "logs/")
```

## Security Considerations

- Account keys and connection strings are sensitive credentials
- The server does not log or expose these secrets in responses
- Use environment variables for production deployments
- Consider using Azure Managed Identity for enhanced security in Azure environments

## Error Handling

The server provides comprehensive error handling for:
- Azure API errors
- Configuration errors
- Container access issues
- Network connectivity problems

All errors are returned in a structured JSON format with helpful error messages.

## Extensibility

The server is designed to be easily extensible. You can add new tools for:
- Blob metadata analysis
- Container property inspection
- Blob lifecycle management
- Access tier monitoring
- And more Azure Storage features

## Dependencies

- `azure-storage-blob>=12.19.0`: Azure Blob Storage SDK
- `azure-core>=1.29.0`: Azure Core SDK
- `mcp`: Model Context Protocol library

## Version

Current version: 1.0.0

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
