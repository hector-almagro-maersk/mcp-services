import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test utility functions that don't require kubernetes
from server import (
    get_kubeconfig_path,
    get_namespace,
    get_context,
    read_file,
    parse_changelog
)


class TestUtilityFunctions(unittest.TestCase):
    
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
    
    def test_read_file(self):
        """Test file reading functionality."""
        # Create a temporary file
        test_content = "test content\nline 2"
        with open("/tmp/test_file.txt", "w") as f:
            f.write(test_content)
        
        result = read_file("/tmp/test_file.txt")
        self.assertEqual(result, test_content)
        
        # Clean up
        os.remove("/tmp/test_file.txt")
    
    def test_parse_changelog(self):
        """Test changelog parsing functionality."""
        changelog_content = """
# Changelog

## [1.0.0] - 2025-07-09

### Added
- Initial release
- Basic functionality

### Fixed
- Bug fixes

## [0.9.0] - 2025-07-08

### Added
- Beta features
"""
        
        result = parse_changelog(changelog_content)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["version"], "1.0.0")
        self.assertEqual(result[0]["date"], "2025-07-09")
        self.assertIn("Added", result[0]["changes"])
        self.assertIn("Fixed", result[0]["changes"])
        self.assertEqual(len(result[0]["changes"]["Added"]), 2)
        self.assertEqual(len(result[0]["changes"]["Fixed"]), 1)
    
    def test_format_pod_info_mock(self):
        """Test pod information formatting with mocked data."""
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
        
        # Import format_pod_info only when needed to avoid kubernetes import issues
        try:
            from server import format_pod_info
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
        except ImportError:
            # Skip this test if kubernetes is not available
            self.skipTest("Kubernetes library not available")


class TestVersionFunction(unittest.TestCase):
    """Test version-related functionality."""
    
    def test_version_file_exists(self):
        """Test that VERSION file exists and is readable."""
        version_path = os.path.join(os.path.dirname(__file__), "VERSION")
        self.assertTrue(os.path.exists(version_path))
        
        with open(version_path, "r") as f:
            version = f.read().strip()
            self.assertRegex(version, r"^\d+\.\d+\.\d+$")
    
    def test_changelog_file_exists(self):
        """Test that CHANGELOG.md file exists and is readable."""
        changelog_path = os.path.join(os.path.dirname(__file__), "CHANGELOG.md")
        self.assertTrue(os.path.exists(changelog_path))
        
        with open(changelog_path, "r") as f:
            content = f.read()
            self.assertIn("# Changelog", content)
            self.assertIn("1.0.0", content)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
