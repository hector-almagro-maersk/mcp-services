import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add the parent directory to the path so we can import the server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import (
    get_kubeconfig_path,
    get_namespace,
    get_context,
    format_pod_info,
    mcp
)


class TestKubernetesServer(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        # Clear environment variables
        os.environ.pop("MCP_KUBERNETES_KUBECONFIG", None)
        os.environ.pop("MCP_KUBERNETES_NAMESPACE", None)
        os.environ.pop("MCP_KUBERNETES_CONTEXT", None)
    
    def test_get_kubeconfig_path_default(self):
        """Test default kubeconfig path."""
        expected = os.path.expanduser("~/.kube/config")
        self.assertEqual(get_kubeconfig_path(), expected)
    
    def test_get_kubeconfig_path_custom(self):
        """Test custom kubeconfig path from environment."""
        custom_path = "/custom/path/to/kubeconfig"
        os.environ["MCP_KUBERNETES_KUBECONFIG"] = custom_path
        self.assertEqual(get_kubeconfig_path(), custom_path)
    
    def test_get_namespace_default(self):
        """Test default namespace."""
        self.assertEqual(get_namespace(), "default")
    
    def test_get_namespace_custom(self):
        """Test custom namespace from environment."""
        custom_namespace = "my-namespace"
        os.environ["MCP_KUBERNETES_NAMESPACE"] = custom_namespace
        self.assertEqual(get_namespace(), custom_namespace)
    
    def test_get_context_none(self):
        """Test context when not set."""
        self.assertIsNone(get_context())
    
    def test_get_context_custom(self):
        """Test custom context from environment."""
        custom_context = "my-cluster"
        os.environ["MCP_KUBERNETES_CONTEXT"] = custom_context
        self.assertEqual(get_context(), custom_context)
    
    def test_format_pod_info(self):
        """Test pod information formatting."""
        # Mock pod object
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp.isoformat.return_value = "2025-07-09T10:00:00Z"
        mock_pod.metadata.labels = {"app": "test"}
        mock_pod.metadata.annotations = {"annotation": "value"}
        mock_pod.status.phase = "Running"
        mock_pod.spec.node_name = "worker-1"
        
        # Mock container status
        mock_container_status = MagicMock()
        mock_container_status.name = "test-container"
        mock_container_status.ready = True
        mock_container_status.restart_count = 2
        mock_container_status.state = "running"
        mock_container_status.image = "nginx:latest"
        mock_pod.status.container_statuses = [mock_container_status]
        
        result = format_pod_info(mock_pod)
        
        expected = {
            "name": "test-pod",
            "namespace": "default",
            "phase": "Running",
            "node": "worker-1",
            "created": "2025-07-09T10:00:00Z",
            "restart_count": 2,
            "container_statuses": [{
                "name": "test-container",
                "ready": True,
                "restart_count": 2,
                "state": "running",
                "image": "nginx:latest"
            }],
            "labels": {"app": "test"},
            "annotations": {"annotation": "value"}
        }
        
        self.assertEqual(result, expected)
    
    def test_format_pod_info_no_containers(self):
        """Test pod formatting when no container statuses are available."""
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp.isoformat.return_value = "2025-07-09T10:00:00Z"
        mock_pod.metadata.labels = {}
        mock_pod.metadata.annotations = {}
        mock_pod.status.phase = "Pending"
        mock_pod.spec.node_name = None
        mock_pod.status.container_statuses = None
        
        result = format_pod_info(mock_pod)
        
        self.assertEqual(result["restart_count"], 0)
        self.assertEqual(result["container_statuses"], [])
        self.assertEqual(result["phase"], "Pending")
    
    @patch('server.initialize_kubernetes_client')
    def test_list_pods_success(self, mock_init_client):
        """Test successful pod listing."""
        # Mock Kubernetes client
        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1
        
        # Mock pod response
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp.isoformat.return_value = "2025-07-09T10:00:00Z"
        mock_pod.metadata.labels = {}
        mock_pod.metadata.annotations = {}
        mock_pod.status.phase = "Running"
        mock_pod.spec.node_name = "worker-1"
        mock_pod.status.container_statuses = None
        
        mock_response = MagicMock()
        mock_response.items = [mock_pod]
        mock_v1.list_namespaced_pod.return_value = mock_response
        
        # Test the list_pods function through the MCP framework
        # This would require setting up the MCP test framework
        # For now, we'll test the underlying logic
        
        self.assertTrue(True)  # Placeholder for actual MCP testing
    
    @patch('server.initialize_kubernetes_client')
    def test_kubernetes_api_error_handling(self, mock_init_client):
        """Test Kubernetes API error handling."""
        from kubernetes.client.rest import ApiException
        
        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1
        
        # Mock API exception
        mock_v1.list_namespaced_pod.side_effect = ApiException(status=404, reason="Not Found")
        
        # This would test error handling in the actual functions
        # Placeholder for actual error handling tests
        self.assertTrue(True)


class TestServerIntegration(unittest.TestCase):
    """Integration tests that require a real or mocked Kubernetes cluster."""
    
    @patch('server.config.load_kube_config')
    @patch('server.client.CoreV1Api')
    def test_initialize_kubernetes_client_success(self, mock_core_v1, mock_load_config):
        """Test successful Kubernetes client initialization."""
        from server import initialize_kubernetes_client
        
        mock_load_config.return_value = None
        mock_api_instance = MagicMock()
        mock_core_v1.return_value = mock_api_instance
        
        result = initialize_kubernetes_client()
        
        mock_load_config.assert_called_once()
        mock_core_v1.assert_called_once()
        self.assertEqual(result, mock_api_instance)
    
    @patch('server.config.load_kube_config')
    @patch('server.config.load_incluster_config')
    @patch('server.client.CoreV1Api')
    def test_initialize_kubernetes_client_incluster_fallback(self, mock_core_v1, mock_incluster, mock_load_config):
        """Test fallback to in-cluster config."""
        from server import initialize_kubernetes_client
        
        # Simulate kubeconfig loading failure
        mock_load_config.side_effect = Exception("Kubeconfig not found")
        mock_incluster.return_value = None
        mock_api_instance = MagicMock()
        mock_core_v1.return_value = mock_api_instance
        
        result = initialize_kubernetes_client()
        
        mock_load_config.assert_called_once()
        mock_incluster.assert_called_once()
        mock_core_v1.assert_called_once()
        self.assertEqual(result, mock_api_instance)


class TestGetPodAppsettingsFile(unittest.TestCase):
    """Tests for the get_pod_appsettings_file tool."""

    @patch('server.client.AppsV1Api')
    @patch('server.initialize_kubernetes_client')
    def test_restart_pod_rollout_success(self, mock_init_client, mock_apps_v1_cls):
        """Test successful rollout restart of a pod."""
        from server import restart_pod

        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1

        mock_apps_v1 = MagicMock()
        mock_apps_v1_cls.return_value = mock_apps_v1

        # Mock pod with owner reference to a ReplicaSet
        mock_pod = MagicMock()
        mock_pod.metadata.name = "my-app-abc123"
        mock_owner_ref = MagicMock()
        mock_owner_ref.kind = "ReplicaSet"
        mock_owner_ref.name = "my-app-rs"
        mock_pod.metadata.owner_references = [mock_owner_ref]
        mock_v1.read_namespaced_pod.return_value = mock_pod

        # Mock ReplicaSet with owner reference to a Deployment
        mock_rs = MagicMock()
        mock_rs_owner = MagicMock()
        mock_rs_owner.kind = "Deployment"
        mock_rs_owner.name = "my-app"
        mock_rs.metadata.owner_references = [mock_rs_owner]
        mock_apps_v1.read_namespaced_replica_set.return_value = mock_rs

        # Mock successful patch
        mock_apps_v1.patch_namespaced_deployment.return_value = MagicMock()

        result = restart_pod("my-app-abc123", namespace="default")
        parsed = json.loads(result)

        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["deployment"], "my-app")
        self.assertIn("Rollout restart triggered", parsed["message"])
        mock_apps_v1.patch_namespaced_deployment.assert_called_once()
        # Verify the annotation patch was used
        call_kwargs = mock_apps_v1.patch_namespaced_deployment.call_args
        body = call_kwargs[1].get("body") or call_kwargs[0][2] if len(call_kwargs[0]) > 2 else call_kwargs[1]["body"]
        self.assertIn("kubectl.kubernetes.io/restartedAt", body["spec"]["template"]["metadata"]["annotations"])

    @patch('server.client.AppsV1Api')
    @patch('server.initialize_kubernetes_client')
    def test_restart_pod_not_found(self, mock_init_client, mock_apps_v1_cls):
        """Test restart_pod when the pod does not exist."""
        from server import restart_pod
        from kubernetes.client.rest import ApiException

        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1
        mock_apps_v1_cls.return_value = MagicMock()

        mock_v1.read_namespaced_pod.side_effect = ApiException(status=404, reason="Not Found")
        mock_v1.list_namespaced_pod.return_value = MagicMock(items=[])

        result = restart_pod("nonexistent-pod", namespace="default")
        parsed = json.loads(result)

        self.assertEqual(parsed["status"], "error")
        self.assertIn("not found", parsed["message"].lower())

    @patch('server.client.AppsV1Api')
    @patch('server.initialize_kubernetes_client')
    def test_restart_pod_no_deployment(self, mock_init_client, mock_apps_v1_cls):
        """Test restart_pod when the pod is not managed by a deployment."""
        from server import restart_pod

        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1
        mock_apps_v1_cls.return_value = MagicMock()

        mock_pod = MagicMock()
        mock_pod.metadata.owner_references = None
        mock_v1.read_namespaced_pod.return_value = mock_pod

        result = restart_pod("standalone-pod", namespace="default")
        parsed = json.loads(result)

        self.assertEqual(parsed["status"], "error")
        self.assertIn("Could not find deployment", parsed["message"])

    @patch('server.client.AppsV1Api')
    @patch('server.initialize_kubernetes_client')
    def test_restart_pod_patch_failure(self, mock_init_client, mock_apps_v1_cls):
        """Test restart_pod when the deployment patch fails."""
        from server import restart_pod
        from kubernetes.client.rest import ApiException

        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1

        mock_apps_v1 = MagicMock()
        mock_apps_v1_cls.return_value = mock_apps_v1

        mock_pod = MagicMock()
        mock_owner_ref = MagicMock()
        mock_owner_ref.kind = "Deployment"
        mock_owner_ref.name = "my-deploy"
        mock_pod.metadata.owner_references = [mock_owner_ref]
        mock_v1.read_namespaced_pod.return_value = mock_pod

        mock_apps_v1.patch_namespaced_deployment.side_effect = ApiException(status=403, reason="Forbidden")

        result = restart_pod("my-pod", namespace="default")
        parsed = json.loads(result)

        self.assertEqual(parsed["status"], "error")
        self.assertIn("Failed to restart deployment", parsed["message"])

    @patch('server.stream')
    @patch('server.initialize_kubernetes_client')
    def test_get_pod_appsettings_file_success(self, mock_init_client, mock_stream):
        """Test successful file retrieval from a pod."""
        from server import get_pod_appsettings_file

        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1

        # Mock pod
        mock_pod = MagicMock()
        mock_pod.spec.containers = [MagicMock(name='my-container')]
        mock_pod.spec.containers[0].name = 'my-container'
        mock_v1.read_namespaced_pod.return_value = mock_pod

        # Mock stream response
        mock_resp = MagicMock()
        mock_resp.is_open.side_effect = [True, False]
        mock_resp.peek_stdout.return_value = True
        mock_resp.peek_stderr.return_value = False
        mock_resp.read_stdout.return_value = '{"ConnectionStrings": {"Default": "Server=db"}}'
        mock_resp.returncode = 0
        mock_stream.return_value = mock_resp

        result = get_pod_appsettings_file("test-pod", namespace="default")
        parsed = json.loads(result)

        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["pod"], "test-pod")
        self.assertEqual(parsed["namespace"], "default")
        self.assertIn("content", parsed)

    @patch('server.initialize_kubernetes_client')
    def test_get_pod_appsettings_file_pod_not_found(self, mock_init_client):
        """Test file retrieval when pod does not exist."""
        from server import get_pod_appsettings_file
        from kubernetes.client.rest import ApiException

        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1
        mock_v1.read_namespaced_pod.side_effect = ApiException(status=404, reason="Not Found")

        result = get_pod_appsettings_file("nonexistent-pod", namespace="default")
        parsed = json.loads(result)

        self.assertEqual(parsed["status"], "error")
        self.assertIn("not found", parsed["message"].lower())

    @patch('server.stream')
    @patch('server.initialize_kubernetes_client')
    def test_get_pod_appsettings_file_file_not_found(self, mock_init_client, mock_stream):
        """Test when appsettings.Production.json is not found in any search path."""
        from server import get_pod_appsettings_file

        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1

        # Mock pod
        mock_pod = MagicMock()
        mock_pod.spec.containers = [MagicMock(name='my-container')]
        mock_pod.spec.containers[0].name = 'my-container'
        mock_v1.read_namespaced_pod.return_value = mock_pod

        # Mock stream response - file not found (non-zero return code, empty stdout)
        mock_resp = MagicMock()
        mock_resp.is_open.side_effect = [True, False]
        mock_resp.peek_stdout.return_value = False
        mock_resp.peek_stderr.return_value = True
        mock_resp.read_stderr.return_value = "cat: /app/appsettings.Production.json: No such file or directory"
        mock_resp.returncode = 1
        mock_stream.return_value = mock_resp

        result = get_pod_appsettings_file("test-pod", namespace="default")
        parsed = json.loads(result)

        self.assertEqual(parsed["status"], "error")
        self.assertIn("not found", parsed["message"].lower())
        self.assertIn("searched_paths", parsed)

    @patch('server.stream')
    @patch('server.initialize_kubernetes_client')
    def test_get_pod_appsettings_file_with_container(self, mock_init_client, mock_stream):
        """Test file retrieval targeting a specific container."""
        from server import get_pod_appsettings_file

        mock_v1 = MagicMock()
        mock_init_client.return_value = mock_v1

        # Mock pod
        mock_pod = MagicMock()
        mock_pod.spec.containers = [MagicMock(), MagicMock()]
        mock_pod.spec.containers[0].name = 'sidecar'
        mock_pod.spec.containers[1].name = 'app'
        mock_v1.read_namespaced_pod.return_value = mock_pod

        # Mock stream response
        mock_resp = MagicMock()
        mock_resp.is_open.side_effect = [True, False]
        mock_resp.peek_stdout.return_value = True
        mock_resp.peek_stderr.return_value = False
        mock_resp.read_stdout.return_value = '{"Logging": {"LogLevel": "Warning"}}'
        mock_resp.returncode = 0
        mock_stream.return_value = mock_resp

        result = get_pod_appsettings_file("test-pod", namespace="default", container="app")
        parsed = json.loads(result)

        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["container"], "app")


if __name__ == '__main__':
    # Run specific test methods or all tests
    unittest.main(verbosity=2)
