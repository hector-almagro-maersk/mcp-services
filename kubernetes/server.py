import os
import re
import urllib3
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
        
        # Configure SSL settings to handle certificate issues
        configuration = client.Configuration.get_default_copy()
        configuration.verify_ssl = False
        configuration.ssl_ca_cert = None
        client.Configuration.set_default(configuration)
        
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


@mcp.tool(description="Authenticate with Azure AD for AKS cluster access.")
def azure_login() -> str:
    """
    Authenticate with Azure AD to access AKS clusters.
    This tool helps resolve 403 Forbidden errors by refreshing Azure AD tokens.
    
    Returns:
        Status message about the authentication process.
    """
    try:
        import subprocess
        import json
        
        # Run azure login command
        result = subprocess.run(['az', 'login'], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Try to get account info to confirm login
            account_result = subprocess.run(['az', 'account', 'show'], capture_output=True, text=True)
            if account_result.returncode == 0:
                account_info = json.loads(account_result.stdout)
                return json.dumps({
                    "status": "success",
                    "message": "Successfully authenticated with Azure AD",
                    "user": account_info.get("user", {}).get("name", "Unknown"),
                    "subscription": account_info.get("name", "Unknown"),
                    "tenant": account_info.get("tenantId", "Unknown"),
                    "next_steps": [
                        "You can now use Kubernetes tools to access your AKS clusters",
                        "If you still get 403 errors, check your RBAC permissions in the cluster"
                    ]
                }, indent=2)
            else:
                return json.dumps({
                    "status": "partial_success",
                    "message": "Azure login completed but couldn't verify account details",
                    "output": result.stdout,
                    "next_steps": [
                        "Try running Kubernetes commands again",
                        "If issues persist, check cluster permissions"
                    ]
                }, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": "Azure login failed",
                "error": result.stderr,
                "suggestions": [
                    "Make sure Azure CLI is installed",
                    "Check your internet connection",
                    "Try running 'az login --use-device-code' if browser login fails"
                ]
            }, indent=2)
    except FileNotFoundError:
        return json.dumps({
            "status": "error",
            "message": "Azure CLI not found",
            "error": "Azure CLI (az) is not installed or not in PATH",
            "installation_help": {
                "macOS": "brew install azure-cli",
                "ubuntu": "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash",
                "windows": "Download from https://aka.ms/installazurecliwindows"
            }
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Unexpected error during Azure authentication: {e}",
            "suggestions": [
                "Check if Azure CLI is properly installed",
                "Try manual login with 'az login' in terminal"
            ]
        }, indent=2)


@mcp.tool(description="Check current Azure authentication status and subscription.")
def azure_status() -> str:
    """
    Check the current Azure authentication status and active subscription.
    Useful for troubleshooting authentication issues.
    
    Returns:
        JSON string containing current Azure authentication status.
    """
    try:
        import subprocess
        import json
        
        # Check if user is logged in
        result = subprocess.run(['az', 'account', 'show'], capture_output=True, text=True)
        
        if result.returncode == 0:
            account_info = json.loads(result.stdout)
            
            # Get list of subscriptions
            subs_result = subprocess.run(['az', 'account', 'list'], capture_output=True, text=True)
            subscriptions = []
            if subs_result.returncode == 0:
                subs_data = json.loads(subs_result.stdout)
                subscriptions = [
                    {
                        "name": sub.get("name"),
                        "id": sub.get("id"),
                        "state": sub.get("state"),
                        "isDefault": sub.get("isDefault", False)
                    }
                    for sub in subs_data
                ]
            
            return json.dumps({
                "status": "authenticated",
                "user": account_info.get("user", {}).get("name"),
                "current_subscription": {
                    "name": account_info.get("name"),
                    "id": account_info.get("id"),
                    "tenant_id": account_info.get("tenantId")
                },
                "available_subscriptions": subscriptions,
                "kubernetes_context": get_context(),
                "kubernetes_namespace": get_namespace()
            }, indent=2)
        else:
            return json.dumps({
                "status": "not_authenticated",
                "message": "Not logged in to Azure",
                "error": result.stderr.strip() if result.stderr else "No active Azure session",
                "suggestion": "Run azure_login tool to authenticate"
            }, indent=2)
    except FileNotFoundError:
        return json.dumps({
            "status": "error",
            "message": "Azure CLI not found",
            "error": "Azure CLI (az) is not installed or not in PATH"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error checking Azure status: {e}"
        }, indent=2)


@mcp.tool(description="Restart a pod by scaling its deployment to 0 and then back to 1 replica automatically.")
def restart_pod(pod_name: str, namespace: Optional[str] = None) -> str:
    """
    Restart a pod by scaling its deployment to 0 replicas and then back to 1.
    This is useful for restarting pods that are stuck or need a fresh start.
    
    Args:
        pod_name: Name of the pod to restart
        namespace: Optional namespace where the pod is located. If not provided, uses the configured default namespace.
    
    Returns:
        JSON string containing the restart operation status and steps.
    """
    try:
        import json
        import time
        
        # Initialize both v1 and apps_v1 clients
        v1 = initialize_kubernetes_client()
        apps_v1 = client.AppsV1Api()
        target_namespace = namespace or get_namespace()
        
        # First, try to get the pod to find its deployment/replicaset
        pod = None
        deployment_name = None
        
        try:
            pod = v1.read_namespaced_pod(name=pod_name, namespace=target_namespace)
        except ApiException as e:
            if e.status == 404:
                # If exact pod name not found, try to find by app label
                pods = v1.list_namespaced_pod(
                    namespace=target_namespace, 
                    label_selector=f"app={pod_name}"
                )
                if pods.items:
                    pod = pods.items[0]  # Take the first pod if multiple exist
                    steps.append(f"Found pod '{pod.metadata.name}' by app label '{pod_name}'")
                else:
                    return json.dumps({
                        "status": "error",
                        "message": f"Pod '{pod_name}' not found in namespace '{target_namespace}' and no pods found with app label '{pod_name}'"
                    })
            else:
                raise
        
        # Find the deployment that owns this pod
        deployment_name = None
        if pod.metadata.owner_references:
            for owner in pod.metadata.owner_references:
                if owner.kind == "ReplicaSet":
                    # Get the ReplicaSet to find its deployment
                    try:
                        replicaset = apps_v1.read_namespaced_replica_set(
                            name=owner.name, namespace=target_namespace
                        )
                        if replicaset.metadata.owner_references:
                            for rs_owner in replicaset.metadata.owner_references:
                                if rs_owner.kind == "Deployment":
                                    deployment_name = rs_owner.name
                                    break
                    except ApiException:
                        pass
                elif owner.kind == "Deployment":
                    deployment_name = owner.name
                    break
        
        if not deployment_name:
            return json.dumps({
                "status": "error",
                "message": f"Could not find deployment for pod '{pod_name}'. Pod may not be managed by a deployment."
            })
        
        steps = []
        
        # Step 1: Scale deployment to 0
        try:
            deployment = apps_v1.read_namespaced_deployment(
                name=deployment_name, namespace=target_namespace
            )
            original_replicas = deployment.spec.replicas
            
            # Use scale subresource for more reliable scaling
            scale_body = {
                "spec": {
                    "replicas": 0
                }
            }
            apps_v1.patch_namespaced_deployment_scale(
                name=deployment_name, 
                namespace=target_namespace, 
                body=scale_body
            )
            steps.append(f"Scaled deployment '{deployment_name}' to 0 replicas")
            
            # Wait for pod to be terminated (with timeout)
            max_wait = 60  # 60 seconds timeout
            wait_time = 0
            while wait_time < max_wait:
                try:
                    v1.read_namespaced_pod(name=pod_name, namespace=target_namespace)
                    time.sleep(2)
                    wait_time += 2
                except ApiException as e:
                    if e.status == 404:
                        steps.append(f"Pod '{pod_name}' successfully terminated")
                        break
                    else:
                        raise
            
            if wait_time >= max_wait:
                steps.append(f"Warning: Pod '{pod_name}' still exists after {max_wait} seconds")
            
            # Step 2: Scale deployment back to original replicas (or 1 if original was 0)
            target_replicas = max(original_replicas or 1, 1)
            scale_body = {
                "spec": {
                    "replicas": target_replicas
                }
            }
            apps_v1.patch_namespaced_deployment_scale(
                name=deployment_name, 
                namespace=target_namespace, 
                body=scale_body
            )
            steps.append(f"Scaled deployment '{deployment_name}' back to {target_replicas} replica(s)")
            
            # Wait a bit for new pod to start
            time.sleep(5)
            
            # Get the new pod status
            pods = v1.list_namespaced_pod(
                namespace=target_namespace, 
                label_selector=f"app={deployment_name}"
            )
            
            new_pods = []
            for p in pods.items:
                new_pods.append({
                    "name": p.metadata.name,
                    "phase": p.status.phase,
                    "ready": all(container.ready for container in (p.status.container_statuses or [])),
                    "created": p.metadata.creation_timestamp.isoformat() if p.metadata.creation_timestamp else None
                })
            
            return json.dumps({
                "status": "success",
                "message": f"Pod restart completed successfully",
                "deployment": deployment_name,
                "namespace": target_namespace,
                "steps": steps,
                "new_pods": new_pods,
                "original_replicas": original_replicas,
                "target_replicas": target_replicas,
                "original_pod": pod_name
            }, indent=2)
            
        except ApiException as e:
            # If scaling back fails, try to restore original replicas
            if len(steps) > 0 and "scaled" in steps[-1].lower():
                try:
                    scale_body = {
                        "spec": {
                            "replicas": original_replicas or 1
                        }
                    }
                    apps_v1.patch_namespaced_deployment_scale(
                        name=deployment_name, 
                        namespace=target_namespace, 
                        body=scale_body
                    )
                    steps.append(f"Attempted to restore deployment '{deployment_name}' to {original_replicas or 1} replica(s)")
                except:
                    steps.append(f"Failed to restore deployment '{deployment_name}' after error")
            
            return json.dumps({
                "status": "error",
                "message": f"Failed to restart pod: {e.status} - {e.reason}",
                "steps": steps,
                "deployment": deployment_name,
                "namespace": target_namespace
            })
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error restarting pod: {e}"
        })


if __name__ == "__main__":
    mcp.run()
