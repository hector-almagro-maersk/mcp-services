# Kubernetes MCP Server

A Model Context Protocol (MCP) server that provides tools for monitoring and interacting with Kubernetes clusters. This server allows you to list pods, check their health status, monitor restarts, and get detailed information about your Kubernetes workloads.

## Features

- **Pod Management**: List all pods in a namespace with detailed information
- **Health Monitoring**: Identify pods that are not in 'Running' state
- **Restart Tracking**: Find pods that have experienced restarts and track restart counts
- **Detailed Inspection**: Get comprehensive information about specific pods
- **Log Retrieval**: Fetch pod logs for troubleshooting
- **Namespace Management**: List and explore available namespaces
- **Cluster Health**: Get overall cluster health summary
- **Azure Authentication**: Built-in Azure AD login and status checking for AKS clusters
- **Flexible Configuration**: Support for different kubeconfig files, namespaces, and contexts

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have a valid kubeconfig file and access to a Kubernetes cluster.

## Configuration

The server uses environment variables for configuration:

- `MCP_KUBERNETES_KUBECONFIG`: Path to kubeconfig file (default: `~/.kube/config`)
- `MCP_KUBERNETES_NAMESPACE`: Default namespace to operate in (default: `default`)
- `MCP_KUBERNETES_CONTEXT`: Kubectl context to use (optional)

### Example Configuration

Add this to your VS Code `settings.json` file:

```json
{
  "mcp.servers": {
    "kubernetes": {
      "command": "python",
      "args": ["/path/to/kubernetes/server.py"],
      "env": {
        "MCP_KUBERNETES_KUBECONFIG": "/path/to/your/kubeconfig",
        "MCP_KUBERNETES_NAMESPACE": "my-namespace",
        "MCP_KUBERNETES_CONTEXT": "my-cluster-context"
      }
    }
  }
}
```

## Usage

### Running the Server

```bash
python server.py
```

### Available Tools

#### 1. `list_pods`
Lists all pods in the specified namespace.

**Parameters:**
- `namespace` (optional): Namespace to list pods from

**Example Response:**
```json
{
  "namespace": "default",
  "total_pods": 5,
  "pods": [
    {
      "name": "my-app-7d4b9c8f6d-xyz12",
      "namespace": "default",
      "phase": "Running",
      "node": "worker-node-1",
      "restart_count": 0,
      "container_statuses": [...]
    }
  ]
}
```

#### 2. `list_non_running_pods`
Lists pods that are not in 'Running' state.

**Parameters:**
- `namespace` (optional): Namespace to check

#### 3. `list_restarted_pods`
Lists pods that have experienced restarts.

**Parameters:**
- `namespace` (optional): Namespace to check
- `min_restarts` (optional): Minimum number of restarts to filter by (default: 1)

#### 4. `get_pod_details`
Gets detailed information about a specific pod.

**Parameters:**
- `pod_name` (required): Name of the pod to inspect
- `namespace` (optional): Namespace of the pod

#### 5. `get_pod_logs`
Retrieves logs from a specific pod.

**Parameters:**
- `pod_name` (required): Name of the pod
- `namespace` (optional): Namespace of the pod
- `container` (optional): Container name within the pod
- `tail_lines` (optional): Number of lines to tail (default: 100)

#### 6. `list_namespaces`
Lists all namespaces in the cluster.

#### 7. `get_cluster_health`
Provides a summary of cluster health including pod states across all namespaces.

#### 8. `show_version`
Shows the current version and configuration information.

#### 9. `azure_login`
Authenticate with Azure AD for AKS cluster access. Helps resolve 403 Forbidden errors.

**Returns:**
- Authentication status and user information
- Next steps for accessing clusters
- Error handling for common issues

#### 10. `azure_status`
Check current Azure authentication status and subscription information.

**Returns:**
- Current authentication status
- Active subscription details
- Available subscriptions
- Current Kubernetes context and namespace

#### 11. `restart_pod`
Restart a pod by automatically scaling its deployment to 0 and then back to 1 replica.

**Parameters:**
- `pod_name`: Name of the pod to restart
- `namespace` (optional): Namespace where the pod is located

**Returns:**
- Restart operation status
- Deployment name and scaling steps
- New pod information after restart

**Note:** This tool only works with pods managed by deployments. It will automatically find the deployment that owns the pod and perform a rolling restart.

## Pod Information Format

Each pod entry includes:
- `name`: Pod name
- `namespace`: Namespace
- `phase`: Current phase (Running, Pending, Failed, etc.)
- `node`: Node where the pod is scheduled
- `created`: Creation timestamp
- `restart_count`: Total number of container restarts
- `container_statuses`: Detailed container information
- `labels`: Pod labels
- `annotations`: Pod annotations

## Error Handling

The server includes comprehensive error handling:
- Kubernetes API errors with detailed status codes
- Connection issues with kubeconfig
- Resource not found errors
- Invalid namespace or pod names

## Security Considerations

- The server requires valid Kubernetes credentials
- Access is limited to what the configured kubeconfig allows
- All operations are read-only (no modifications to cluster state)
- Logs are retrieved with configurable limits

## Dependencies

- `kubernetes>=28.0.0`: Official Kubernetes Python client
- `mcp`: Model Context Protocol framework

## Development

### Running Tests

```bash
python -m pytest test_server.py
```

### Code Structure

- `server.py`: Main server implementation
- `requirements.txt`: Python dependencies
- `VERSION`: Version information
- `CHANGELOG.md`: Version history and changes
- `README.md`: This documentation

## Azure AKS Authentication

For Azure AKS clusters, you may encounter 403 Forbidden errors when trying to access cluster resources. This typically means you need to authenticate with Azure AD.

### Quick Authentication
Use the built-in authentication tools:

```bash
# Check current authentication status
azure_status

# Login to Azure AD (if not authenticated or tokens expired)
azure_login
```

### Manual Authentication
If you prefer to authenticate manually:

```bash
az login
az account set --subscription "your-subscription-name"
```

### Common Authentication Issues

1. **403 Forbidden**: Your Azure AD tokens have expired
   - Solution: Run `azure_login` tool or `az login` manually

2. **No subscription access**: You don't have access to the subscription containing the AKS cluster
   - Solution: Contact your Azure administrator for proper permissions

3. **RBAC permissions**: You're authenticated but don't have Kubernetes RBAC permissions
   - Solution: Contact your Kubernetes cluster administrator for proper role assignments

## Troubleshooting

### Common Issues

1. **Connection refused**: Check if your kubeconfig is valid and the cluster is accessible
2. **Namespace not found**: Verify the namespace exists in your cluster
3. **Pod not found**: Ensure the pod name is correct and exists in the specified namespace
4. **Permission denied**: Check if your kubeconfig has the necessary permissions

### Debug Mode

Set the environment variable for more verbose output:
```bash
export KUBERNETES_DEBUG=true
```

## License

This project follows the same license as the parent MCP services repository.

## Contributing

Contributions are welcome! Please ensure your changes maintain the existing code style and include appropriate tests.
