# Changelog

All notable changes to the Kubernetes MCP Server will be documented in this file.

## [1.0.0] - 2025-07-09

### Added
- Initial release of Kubernetes MCP Server
- Support for connecting to Kubernetes clusters via kubeconfig
- List all pods in a specified namespace
- Identify pods not in 'Running' state
- Track pod restart counts and history
- Get detailed pod information including container statuses
- Retrieve pod logs for troubleshooting
- List all namespaces in the cluster
- Cluster health summary across all namespaces
- Environment variable configuration for kubeconfig path, namespace, and context
- Comprehensive error handling and validation
- JSON-formatted responses for all operations

### Features
- **list_pods**: Get comprehensive information about all pods in a namespace
- **list_non_running_pods**: Filter and display pods that are not running
- **list_restarted_pods**: Find pods that have experienced restarts
- **get_pod_details**: Deep dive into specific pod information
- **get_pod_logs**: Retrieve pod logs for debugging
- **list_namespaces**: Explore available namespaces
- **get_cluster_health**: Overall cluster health monitoring
- **show_version**: Display version and configuration information

### Configuration
- `MCP_KUBERNETES_KUBECONFIG`: Path to kubeconfig file (default: ~/.kube/config)
- `MCP_KUBERNETES_NAMESPACE`: Default namespace to operate in (default: default)
- `MCP_KUBERNETES_CONTEXT`: Kubectl context to use (optional)
