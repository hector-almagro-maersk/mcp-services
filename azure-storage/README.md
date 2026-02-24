# Azure Storage MCP Server

An MCP (Model Context Protocol) server for monitoring Azure Blob Storage containers. This server allows you to check if containers contain files and provides detailed information about blob storage resources.

## Features

- **Container Monitoring**: Check if configured containers contain any blobs
- **Flexible Authentication**: Support for both connection strings and account key authentication
- **Detailed Reporting**: Get comprehensive information about containers and their contents
- **Blob Listing**: List blobs in specific containers with optional filtering
- **Blob Download**: Generate temporary SAS-based download URLs for individual blobs
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

### `download_blob(container_name, blob_name, expiry_minutes=5)`
Generates a temporary, read-only SAS download URL for a specific blob.

Azure Blob URLs **without a SAS token are not downloadable** by external clients — Azure requires OAuth, an account key, or a SAS for every request. This tool uses the server-side credentials to generate a short-lived, single-blob, read-only SAS URL that the client can open directly in a browser to download the file. The client never needs (or receives) any storage credentials.

**Parameters:**
- `container_name`: The name of the container where the blob is stored
- `blob_name`: The full name (path) of the blob to download
- `expiry_minutes`: Number of minutes the download link remains valid (default: 5, max: 60)

**Returns:** JSON with `download_url`, expiry info, file size, content type and last modified date.

**Security:**
- SAS is scoped to a single blob with read-only permission
- Link expires automatically after the configured time (default 5 minutes)
- `Content-Disposition: attachment` header forces a file download in browsers
- Blob names with special characters are URL-encoded automatically

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

# Generate a download URL for a blob (valid for 5 minutes, the default)
download_blob("my-container", "reports/monthly.csv")

# Generate a download URL valid for 30 minutes
download_blob("my-container", "reports/monthly.csv", 30)
```

## Security Considerations

- **Blob URLs without SAS are not downloadable.** Azure Blob Storage requires OAuth, an account key, or a SAS token for every request. Raw blob URLs are internal identifiers, not downloadable resources.
- The `download_blob` tool generates a **short-lived, read-only SAS URL** on-demand so the client can download directly from Azure without needing any storage credentials.
- Account keys and connection strings are sensitive credentials that stay server-side.
- The server does not log or expose secrets in responses.
- Use environment variables for production deployments.
- Consider using Azure Managed Identity for enhanced security in Azure environments.

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

Current version: 1.2.0

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
