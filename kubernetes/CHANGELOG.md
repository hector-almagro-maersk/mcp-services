# Changelog

All notable changes to the Kubernetes MCP Server will be documented in this file.

## [1.2.0] - 2026-02-10

### Added
- **get_pod_appsettings_file**: New tool to read the `appsettings.Production.json` configuration file from a running pod via the Kubernetes exec API. Automatically searches common .NET application paths (`/app/`, `/app/config/`, `/`). Supports specifying a target container and returns pretty-printed JSON content.

## [1.1.1] - 2025-11-06

### Fixed
- Prevent UnboundLocalError in `restart_pod` when falling back to label-based pod lookup by initializing the internal `steps` list early so it can be appended to from any code path.
- Make kubeconfig loading more robust: if `load_kube_config` raises (for example when the kubeconfig is missing or invalid), the client now attempts `load_incluster_config()` as a fallback.

### Tests
- Added minor robustness improvements and verified existing unit tests for the kubernetes MCP server pass locally.

## [1.1.0] - 2025-07-09

### Added
- **Azure AD Authentication Support**: New tools for managing Azure authentication for AKS clusters
- **azure_login**: Interactive Azure AD login for AKS cluster access
- **azure_status**: Check current Azure authentication status and active subscription
- **restart_pod**: Restart a pod by automatically scaling its deployment to 0 and then back to 1 replica
- Enhanced troubleshooting capabilities for authentication issues
- Support for Azure CLI integration and token management
- Pod restart functionality for stuck or problematic pods

### Improved
- Better error handling for authentication failures (401/403 errors)
- Enhanced documentation with Azure authentication workflow
- Troubleshooting guide for common authentication scenarios

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
- **azure_login**: Authenticate with Azure AD for AKS access
- **azure_status**: Check Azure authentication status
- **restart_pod**: Restart pods by scaling deployment to 0 and back to 1 replica
- **show_version**: Display version and configuration information

### Configuration
- `MCP_KUBERNETES_KUBECONFIG`: Path to kubeconfig file (default: ~/.kube/config)
- `MCP_KUBERNETES_NAMESPACE`: Default namespace to operate in (default: default)
- `MCP_KUBERNETES_CONTEXT`: Kubectl context to use (optional)
