import os
import re
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def get_kubeconfig_path() -> str:
    """Retrieve the kubeconfig path from environment variable or use default."""
    return os.environ.get("MCP_KUBERNETES_KUBECONFIG", os.path.expanduser("~/.kube/config"))


def get_namespace() -> str:
    """Retrieve the target namespace from environment variable or use default."""
    return os.environ.get("MCP_KUBERNETES_NAMESPACE", "default")


def get_context() -> Optional[str]:
    """Retrieve the kubectl context from environment variable."""
    return os.environ.get("MCP_KUBERNETES_CONTEXT")


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


def initialize_kubernetes_client():
    """Initialize and configure the Kubernetes client."""
    try:
        kubeconfig_path = get_kubeconfig_path()
        context = get_context()
        
        if os.path.exists(kubeconfig_path):
            config.load_kube_config(config_file=kubeconfig_path, context=context)
        else:
            # Try in-cluster config (for when running inside a pod)
            config.load_incluster_config()
        
        return client.CoreV1Api()
    except Exception as e:
        raise Exception(f"Failed to initialize Kubernetes client: {e}")


def format_pod_info(pod) -> Dict[str, Any]:
    """Format pod information into a standardized dictionary."""
    restart_count = 0
    container_statuses = []
    
    if pod.status.container_statuses:
        for container_status in pod.status.container_statuses:
            restart_count += container_status.restart_count
            container_statuses.append({
                "name": container_status.name,
                "ready": container_status.ready,
                "restart_count": container_status.restart_count,
                "state": str(container_status.state),
                "image": container_status.image
            })
    
    return {
        "name": pod.metadata.name,
        "namespace": pod.metadata.namespace,
        "phase": pod.status.phase,
        "node": pod.spec.node_name,
        "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
        "restart_count": restart_count,
        "container_statuses": container_statuses,
        "labels": pod.metadata.labels or {},
        "annotations": pod.metadata.annotations or {}
    }


mcp = FastMCP("MCP Kubernetes Cluster Monitor")


@mcp.tool(description="Show the current MCP version and the full changelog as structured JSON.")
def show_version() -> str:
    """Return the MCP version and the full changelog as JSON: [{version, date, changes: {type: [list]}}]."""
    try:
        import json
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
            "kubernetes_config": {
                "kubeconfig_path": get_kubeconfig_path(),
                "namespace": get_namespace(),
                "context": get_context()
            }
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        import json
        return json.dumps({"error": f"Error reading version or changelog: {e}"})


@mcp.tool(description="List all pods in the configured Kubernetes cluster and namespace.")
def list_pods(namespace: Optional[str] = None) -> str:
    """
    List all pods in the specified namespace or the default configured namespace.
    
    Args:
        namespace: Optional namespace to list pods from. If not provided, uses the configured default namespace.
    
    Returns:
        JSON string containing detailed information about all pods.
    """
    try:
        import json
        v1 = initialize_kubernetes_client()
        target_namespace = namespace or get_namespace()
        
        pods = v1.list_namespaced_pod(namespace=target_namespace)
        
        pod_list = []
        for pod in pods.items:
            pod_info = format_pod_info(pod)
            pod_list.append(pod_info)
        
        result = {
            "namespace": target_namespace,
            "total_pods": len(pod_list),
            "pods": pod_list
        }
        
        return json.dumps(result, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e.status} - {e.reason}"
    except Exception as e:
        return f"Error listing pods: {e}"


@mcp.tool(description="List pods that are not in 'Running' state.")
def list_non_running_pods(namespace: Optional[str] = None) -> str:
    """
    List all pods that are not in the 'Running' state.
    
    Args:
        namespace: Optional namespace to check. If not provided, uses the configured default namespace.
    
    Returns:
        JSON string containing information about pods that are not running.
    """
    try:
        import json
        v1 = initialize_kubernetes_client()
        target_namespace = namespace or get_namespace()
        
        pods = v1.list_namespaced_pod(namespace=target_namespace)
        
        non_running_pods = []
        for pod in pods.items:
            if pod.status.phase != "Running":
                pod_info = format_pod_info(pod)
                non_running_pods.append(pod_info)
        
        result = {
            "namespace": target_namespace,
            "total_non_running_pods": len(non_running_pods),
            "non_running_pods": non_running_pods
        }
        
        return json.dumps(result, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e.status} - {e.reason}"
    except Exception as e:
        return f"Error listing non-running pods: {e}"


@mcp.tool(description="List pods that have experienced restarts.")
def list_restarted_pods(namespace: Optional[str] = None, min_restarts: int = 1) -> str:
    """
    List all pods that have experienced restarts.
    
    Args:
        namespace: Optional namespace to check. If not provided, uses the configured default namespace.
        min_restarts: Minimum number of restarts to filter by (default: 1).
    
    Returns:
        JSON string containing information about pods that have been restarted.
    """
    try:
        import json
        v1 = initialize_kubernetes_client()
        target_namespace = namespace or get_namespace()
        
        pods = v1.list_namespaced_pod(namespace=target_namespace)
        
        restarted_pods = []
        for pod in pods.items:
            pod_info = format_pod_info(pod)
            if pod_info["restart_count"] >= min_restarts:
                restarted_pods.append(pod_info)
        
        result = {
            "namespace": target_namespace,
            "min_restarts_filter": min_restarts,
            "total_restarted_pods": len(restarted_pods),
            "restarted_pods": restarted_pods
        }
        
        return json.dumps(result, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e.status} - {e.reason}"
    except Exception as e:
        return f"Error listing restarted pods: {e}"


@mcp.tool(description="Get detailed information about a specific pod.")
def get_pod_details(pod_name: str, namespace: Optional[str] = None) -> str:
    """
    Get detailed information about a specific pod.
    
    Args:
        pod_name: Name of the pod to inspect.
        namespace: Optional namespace. If not provided, uses the configured default namespace.
    
    Returns:
        JSON string containing detailed pod information.
    """
    try:
        import json
        v1 = initialize_kubernetes_client()
        target_namespace = namespace or get_namespace()
        
        pod = v1.read_namespaced_pod(name=pod_name, namespace=target_namespace)
        pod_info = format_pod_info(pod)
        
        # Add additional details
        pod_info["conditions"] = []
        if pod.status.conditions:
            for condition in pod.status.conditions:
                pod_info["conditions"].append({
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                    "last_transition_time": condition.last_transition_time.isoformat() if condition.last_transition_time else None
                })
        
        # Add resource requests and limits
        pod_info["resources"] = {}
        if pod.spec.containers:
            for i, container in enumerate(pod.spec.containers):
                container_resources = {
                    "name": container.name,
                    "requests": {},
                    "limits": {}
                }
                if container.resources:
                    if container.resources.requests:
                        container_resources["requests"] = dict(container.resources.requests)
                    if container.resources.limits:
                        container_resources["limits"] = dict(container.resources.limits)
                pod_info["resources"][f"container_{i}"] = container_resources
        
        return json.dumps(pod_info, indent=2)
    except ApiException as e:
        if e.status == 404:
            return f"Pod '{pod_name}' not found in namespace '{target_namespace}'"
        return f"Kubernetes API error: {e.status} - {e.reason}"
    except Exception as e:
        return f"Error getting pod details: {e}"


@mcp.tool(description="Get pod logs for troubleshooting.")
def get_pod_logs(pod_name: str, namespace: Optional[str] = None, container: Optional[str] = None, tail_lines: int = 100) -> str:
    """
    Get logs from a specific pod.
    
    Args:
        pod_name: Name of the pod to get logs from.
        namespace: Optional namespace. If not provided, uses the configured default namespace.
        container: Optional container name. If not provided, gets logs from the first container.
        tail_lines: Number of lines to tail from the end of the logs (default: 100).
    
    Returns:
        Pod logs as a string.
    """
    try:
        v1 = initialize_kubernetes_client()
        target_namespace = namespace or get_namespace()
        
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=target_namespace,
            container=container,
            tail_lines=tail_lines
        )
        
        return f"Logs for pod '{pod_name}' in namespace '{target_namespace}':\n\n{logs}"
    except ApiException as e:
        if e.status == 404:
            return f"Pod '{pod_name}' not found in namespace '{target_namespace}'"
        return f"Kubernetes API error: {e.status} - {e.reason}"
    except Exception as e:
        return f"Error getting pod logs: {e}"


@mcp.tool(description="List all namespaces in the cluster.")
def list_namespaces() -> str:
    """
    List all namespaces in the Kubernetes cluster.
    
    Returns:
        JSON string containing information about all namespaces.
    """
    try:
        import json
        v1 = initialize_kubernetes_client()
        
        namespaces = v1.list_namespace()
        
        namespace_list = []
        for ns in namespaces.items:
            namespace_info = {
                "name": ns.metadata.name,
                "status": ns.status.phase,
                "created": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None,
                "labels": ns.metadata.labels or {},
                "annotations": ns.metadata.annotations or {}
            }
            namespace_list.append(namespace_info)
        
        result = {
            "total_namespaces": len(namespace_list),
            "namespaces": namespace_list
        }
        
        return json.dumps(result, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e.status} - {e.reason}"
    except Exception as e:
        return f"Error listing namespaces: {e}"


@mcp.tool(description="Get cluster health summary.")
def get_cluster_health() -> str:
    """
    Get a summary of cluster health including pod states across all namespaces.
    
    Returns:
        JSON string containing cluster health summary.
    """
    try:
        import json
        v1 = initialize_kubernetes_client()
        
        # Get all pods across all namespaces
        all_pods = v1.list_pod_for_all_namespaces()
        
        health_summary = {
            "total_pods": len(all_pods.items),
            "by_phase": {},
            "by_namespace": {},
            "total_restarts": 0,
            "pods_with_restarts": 0
        }
        
        for pod in all_pods.items:
            phase = pod.status.phase
            namespace = pod.metadata.namespace
            
            # Count by phase
            health_summary["by_phase"][phase] = health_summary["by_phase"].get(phase, 0) + 1
            
            # Count by namespace
            if namespace not in health_summary["by_namespace"]:
                health_summary["by_namespace"][namespace] = {
                    "total": 0,
                    "running": 0,
                    "non_running": 0,
                    "total_restarts": 0
                }
            
            health_summary["by_namespace"][namespace]["total"] += 1
            if phase == "Running":
                health_summary["by_namespace"][namespace]["running"] += 1
            else:
                health_summary["by_namespace"][namespace]["non_running"] += 1
            
            # Count restarts
            pod_restarts = 0
            if pod.status.container_statuses:
                for container_status in pod.status.container_statuses:
                    pod_restarts += container_status.restart_count
            
            health_summary["total_restarts"] += pod_restarts
            health_summary["by_namespace"][namespace]["total_restarts"] += pod_restarts
            
            if pod_restarts > 0:
                health_summary["pods_with_restarts"] += 1
        
        return json.dumps(health_summary, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e.status} - {e.reason}"
    except Exception as e:
        return f"Error getting cluster health: {e}"


if __name__ == "__main__":
    mcp.run()
