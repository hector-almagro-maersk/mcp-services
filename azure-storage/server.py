import os
import re
import json
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError


def get_storage_config() -> Dict[str, Any]:
    """Retrieve the Azure Storage configuration from environment variable or config file."""
    config_str = os.environ.get("MCP_AZURE_STORAGE_CONFIG")
    
    if config_str:
        try:
            return json.loads(config_str)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in MCP_AZURE_STORAGE_CONFIG: {e}")
    
    # Try to load from config file
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    
    raise Exception("No Azure Storage configuration found. Set MCP_AZURE_STORAGE_CONFIG environment variable or create config.json")


def read_file(path: str) -> str:
    """Read the contents of a file and return as string."""
    with open(path, "r") as f:
        return f.read()


def parse_changelog(changelog: str) -> List[Dict[str, Any]]:
    """Parse the changelog markdown into a structured list."""
    version_pattern = re.compile(r"^##+\s*\[?v?(\d+\.\d+\.\d+(?:-[^\]\s]+)?)\]?\s*-?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})?\s*$", re.MULTILINE)
    matches = list(version_pattern.finditer(changelog))
    changelog_entries = []
    for i, m in enumerate(matches):
        v = m.group(1)
        date = m.group(2) or None
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(changelog)
        section = changelog[start:end].strip()
        # Find all change types and their lists
        changes = {}
        type_pattern = re.compile(r"^###\s+([A-Za-z ]+)\s*$", re.MULTILINE)
        type_matches = list(type_pattern.finditer(section))
        for j, t in enumerate(type_matches):
            change_type = t.group(1).strip()
            t_start = t.end()
            t_end = type_matches[j+1].start() if j+1 < len(type_matches) else len(section)
            bullets = re.findall(r"^[-*]\s+(.*)$", section[t_start:t_end], re.MULTILINE)
            changes[change_type] = bullets
        changelog_entries.append({
            "version": v,
            "date": date,
            "changes": changes
        })
    return changelog_entries


def create_blob_service_client(container_config: Dict[str, Any]) -> BlobServiceClient:
    """Create a BlobServiceClient for the given container configuration."""
    if "connection_string" in container_config:
        return BlobServiceClient.from_connection_string(container_config["connection_string"])
    elif "account_name" in container_config and "account_key" in container_config:
        account_url = f"https://{container_config['account_name']}.blob.core.windows.net"
        return BlobServiceClient(account_url=account_url, credential=container_config["account_key"])
    else:
        raise ValueError("Container configuration must include either 'connection_string' or both 'account_name' and 'account_key'")


def check_container_has_blobs(container_config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a container has any blobs."""
    try:
        blob_service_client = create_blob_service_client(container_config)
        container_name = container_config["container_name"]
        
        # Get container client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Check if container exists
        if not container_client.exists():
            return {
                "container_name": container_name,
                "exists": False,
                "has_blobs": False,
                "blob_count": 0,
                "error": "Container does not exist"
            }
        
        # List blobs to check if any exist and count them
        blob_iter = container_client.list_blobs()
        blob_count = 0
        has_blobs = False
        
        # Count blobs (limit to reasonable number for performance)
        for i, blob in enumerate(blob_iter):
            blob_count += 1
            has_blobs = True
            # Limit counting to avoid performance issues on large containers
            if i >= 10000:  # Stop counting after 10k blobs
                break
        
        return {
            "container_name": container_name,
            "exists": True,
            "has_blobs": has_blobs,
            "blob_count": blob_count,
            "account_name": container_config.get("account_name", "from_connection_string")
        }
        
    except AzureError as e:
        return {
            "container_name": container_config["container_name"],
            "exists": False,
            "has_blobs": False,
            "blob_count": 0,
            "error": f"Azure error: {str(e)}"
        }
    except Exception as e:
        return {
            "container_name": container_config["container_name"],
            "exists": False,
            "has_blobs": False,
            "blob_count": 0,
            "error": f"Error: {str(e)}"
        }


mcp = FastMCP("MCP Azure Blob Storage Monitor")


@mcp.tool(description="Show the current MCP version and the full changelog as structured JSON.")
def show_version() -> str:
    """Return the MCP version and the full changelog as JSON: [{version, date, changes: {type: [list]}}]."""
    try:
        version_path = os.path.join(os.path.dirname(__file__), "VERSION")
        changelog_path = os.path.join(os.path.dirname(__file__), "CHANGELOG.md")
        
        version = "1.0.0"  # Default version
        if os.path.exists(version_path):
            version = read_file(version_path).strip()
        
        changelog_entries = []
        if os.path.exists(changelog_path):
            changelog = read_file(changelog_path)
            changelog_entries = parse_changelog(changelog)
        
        result = {
            "current_version": version,
            "changelog": changelog_entries,
            "azure_storage_config": {
                "config_source": "MCP_AZURE_STORAGE_CONFIG env var" if os.environ.get("MCP_AZURE_STORAGE_CONFIG") else "config.json file"
            }
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error reading version or changelog: {e}"})


@mcp.tool(description="List all configured Azure Blob Storage containers.")
def list_containers() -> str:
    """
    List all configured Azure Blob Storage containers from the configuration.
    
    Returns:
        JSON string containing information about all configured containers.
    """
    try:
        config = get_storage_config()
        containers = config.get("containers", [])
        
        result = {
            "total_containers": len(containers),
            "containers": []
        }
        
        for container_config in containers:
            container_info = {
                "container_name": container_config.get("container_name"),
                "account_name": container_config.get("account_name", "from_connection_string"),
                "has_connection_string": "connection_string" in container_config,
                "has_account_credentials": "account_name" in container_config and "account_key" in container_config
            }
            result["containers"].append(container_info)
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error listing containers: {e}"})


@mcp.tool(description="Check all configured containers to see which ones contain blobs.")
def check_containers() -> str:
    """
    Check all configured containers to determine which ones contain blobs (files).
    
    Returns:
        JSON string containing detailed information about each container and whether it contains blobs.
    """
    try:
        config = get_storage_config()
        containers = config.get("containers", [])
        
        if not containers:
            return json.dumps({"error": "No containers configured"})
        
        results = []
        for container_config in containers:
            result = check_container_has_blobs(container_config)
            results.append(result)
        
        summary = {
            "total_containers": len(results),
            "containers_with_blobs": len([r for r in results if r.get("has_blobs", False)]),
            "empty_containers": len([r for r in results if r.get("exists", False) and not r.get("has_blobs", False)]),
            "error_containers": len([r for r in results if "error" in r]),
            "results": results
        }
        
        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error checking containers: {e}"})


@mcp.tool(description="Check a specific container to see if it contains blobs.")
def check_container(container_name: str) -> str:
    """
    Check a specific container to determine if it contains blobs (files).
    
    Args:
        container_name: The name of the container to check.
    
    Returns:
        JSON string containing detailed information about the container and whether it contains blobs.
    """
    try:
        config = get_storage_config()
        containers = config.get("containers", [])
        
        # Find the container configuration
        container_config = None
        for config_item in containers:
            if config_item.get("container_name") == container_name:
                container_config = config_item
                break
        
        if not container_config:
            return json.dumps({
                "error": f"Container '{container_name}' not found in configuration",
                "available_containers": [c.get("container_name") for c in containers]
            })
        
        result = check_container_has_blobs(container_config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error checking container '{container_name}': {e}"})


@mcp.tool(description="List blobs in a specific container (up to a specified limit).")
def list_blobs(container_name: str, max_results: int = 10, prefix: str = None) -> str:
    """
    List blobs in a specific container.
    
    Args:
        container_name: The name of the container to list blobs from.
        max_results: Maximum number of blobs to return (default: 10, max: 100).
        prefix: Optional prefix to filter blobs by name.
    
    Returns:
        JSON string containing information about blobs in the container.
    """
    try:
        # Limit max_results to prevent overwhelming responses
        max_results = min(max_results, 100)
        
        config = get_storage_config()
        containers = config.get("containers", [])
        
        # Find the container configuration
        container_config = None
        for config_item in containers:
            if config_item.get("container_name") == container_name:
                container_config = config_item
                break
        
        if not container_config:
            return json.dumps({
                "error": f"Container '{container_name}' not found in configuration",
                "available_containers": [c.get("container_name") for c in containers]
            })
        
        blob_service_client = create_blob_service_client(container_config)
        container_client = blob_service_client.get_container_client(container_name)
        
        if not container_client.exists():
            return json.dumps({
                "error": f"Container '{container_name}' does not exist",
                "container_name": container_name
            })
        
        # List blobs with optional prefix
        list_params = {}
        if prefix:
            list_params["name_starts_with"] = prefix
        
        blob_iter = container_client.list_blobs(**list_params)
        
        blob_list = []
        for i, blob in enumerate(blob_iter):
            if i >= max_results:  # Manually limit results
                break
            blob_info = {
                "name": blob.name,
                "size": blob.size,
                "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                "content_type": blob.content_settings.content_type if blob.content_settings else None,
                "etag": blob.etag
            }
            blob_list.append(blob_info)
        
        result = {
            "container_name": container_name,
            "blob_count": len(blob_list),
            "max_results": max_results,
            "prefix": prefix,
            "blobs": blob_list
        }
        
        return json.dumps(result, indent=2)
    except AzureError as e:
        return json.dumps({"error": f"Azure error listing blobs in '{container_name}': {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Error listing blobs in '{container_name}': {str(e)}"})


if __name__ == "__main__":
    mcp.run()
