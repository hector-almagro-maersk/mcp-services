import unittest
import json
import os
from unittest.mock import patch, MagicMock
from server import (
    get_storage_config,
    create_blob_service_client,
    check_container_has_blobs,
    download_blob,
    mcp
)


class TestAzureStorageServer(unittest.TestCase):
    """Test cases for the Azure Storage MCP server."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_config = {
            "containers": [
                {
                    "container_name": "test-container-1",
                    "account_name": "testaccount",
                    "account_key": "testkey123"
                },
                {
                    "container_name": "test-container-2",
                    "connection_string": "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey123;EndpointSuffix=core.windows.net"
                }
            ]
        }
    
    @patch.dict(os.environ, {"MCP_AZURE_STORAGE_CONFIG": '{"containers": [{"container_name": "env-container", "account_name": "envaccount", "account_key": "envkey"}]}'})
    def test_get_storage_config_from_env(self):
        """Test loading configuration from environment variable."""
        config = get_storage_config()
        self.assertIn("containers", config)
        self.assertEqual(len(config["containers"]), 1)
        self.assertEqual(config["containers"][0]["container_name"], "env-container")
    
    @patch.dict(os.environ, {"MCP_AZURE_STORAGE_CONFIG": 'invalid-json'})
    def test_get_storage_config_invalid_json(self):
        """Test handling of invalid JSON in environment variable."""
        with self.assertRaises(Exception) as context:
            get_storage_config()
        self.assertIn("Invalid JSON", str(context.exception))
    
    def test_create_blob_service_client_with_connection_string(self):
        """Test creating blob service client with connection string."""
        container_config = {
            "container_name": "test-container",
            "connection_string": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net"
        }
        
        with patch('server.BlobServiceClient.from_connection_string') as mock_client:
            mock_client.return_value = MagicMock()
            client = create_blob_service_client(container_config)
            mock_client.assert_called_once_with(container_config["connection_string"])
    
    def test_create_blob_service_client_with_account_key(self):
        """Test creating blob service client with account name and key."""
        container_config = {
            "container_name": "test-container",
            "account_name": "testaccount",
            "account_key": "testkey123"
        }
        
        with patch('server.BlobServiceClient') as mock_client:
            mock_client.return_value = MagicMock()
            client = create_blob_service_client(container_config)
            mock_client.assert_called_once_with(
                account_url="https://testaccount.blob.core.windows.net",
                credential="testkey123"
            )
    
    def test_create_blob_service_client_missing_config(self):
        """Test error handling for missing configuration."""
        container_config = {
            "container_name": "test-container"
            # Missing both connection_string and account credentials
        }
        
        with self.assertRaises(ValueError) as context:
            create_blob_service_client(container_config)
        self.assertIn("Container configuration must include", str(context.exception))
    
    @patch('server.create_blob_service_client')
    def test_check_container_has_blobs_success(self, mock_create_client):
        """Test successful container blob check."""
        # Mock the blob service client and container client
        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_container_client.exists.return_value = True
        mock_container_client.list_blobs.return_value = [MagicMock()]  # Has blobs
        
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_create_client.return_value = mock_blob_service
        
        container_config = {
            "container_name": "test-container",
            "account_name": "testaccount",
            "account_key": "testkey123"
        }
        
        result = check_container_has_blobs(container_config)
        
        self.assertEqual(result["container_name"], "test-container")
        self.assertTrue(result["exists"])
        self.assertTrue(result["has_blobs"])
        self.assertNotIn("error", result)
    
    @patch('server.create_blob_service_client')
    def test_check_container_has_blobs_empty_container(self, mock_create_client):
        """Test checking an empty container."""
        # Mock empty container
        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_container_client.exists.return_value = True
        mock_container_client.list_blobs.return_value = []  # No blobs
        
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_create_client.return_value = mock_blob_service
        
        container_config = {
            "container_name": "empty-container",
            "account_name": "testaccount",
            "account_key": "testkey123"
        }
        
        result = check_container_has_blobs(container_config)
        
        self.assertEqual(result["container_name"], "empty-container")
        self.assertTrue(result["exists"])
        self.assertFalse(result["has_blobs"])
        self.assertEqual(result["blob_count"], 0)
        self.assertNotIn("error", result)
    
    @patch('server.create_blob_service_client')
    def test_check_container_has_blobs_nonexistent_container(self, mock_create_client):
        """Test checking a non-existent container."""
        # Mock non-existent container
        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_container_client.exists.return_value = False
        
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_create_client.return_value = mock_blob_service
        
        container_config = {
            "container_name": "nonexistent-container",
            "account_name": "testaccount",
            "account_key": "testkey123"
        }
        
        result = check_container_has_blobs(container_config)
        
        self.assertEqual(result["container_name"], "nonexistent-container")
        self.assertFalse(result["exists"])
        self.assertFalse(result["has_blobs"])
        self.assertEqual(result["blob_count"], 0)
        self.assertIn("error", result)
        self.assertIn("does not exist", result["error"])


class TestMCPTools(unittest.TestCase):
    """Test the MCP tool functions."""
    
    @patch('server.get_storage_config')
    def test_list_containers_tool(self, mock_get_config):
        """Test the list_containers MCP tool."""
        mock_get_config.return_value = {
            "containers": [
                {
                    "container_name": "test-container-1",
                    "account_name": "testaccount",
                    "account_key": "testkey123"
                },
                {
                    "container_name": "test-container-2",
                    "connection_string": "test-connection-string"
                }
            ]
        }
        
        # Import the tool function
        from server import list_containers
        
        result = list_containers()
        result_data = json.loads(result)
        
        self.assertEqual(result_data["total_containers"], 2)
        self.assertEqual(len(result_data["containers"]), 2)
        self.assertEqual(result_data["containers"][0]["container_name"], "test-container-1")
        self.assertTrue(result_data["containers"][1]["has_connection_string"])
    
    @patch('server.get_storage_config')
    @patch('server.check_container_has_blobs')
    def test_check_containers_tool(self, mock_check_blobs, mock_get_config):
        """Test the check_containers MCP tool."""
        mock_get_config.return_value = {
            "containers": [
                {"container_name": "container-1"},
                {"container_name": "container-2"}
            ]
        }
        
        mock_check_blobs.side_effect = [
            {"container_name": "container-1", "exists": True, "has_blobs": True},
            {"container_name": "container-2", "exists": True, "has_blobs": False}
        ]
        
        # Import the tool function
        from server import check_containers
        
        result = check_containers()
        result_data = json.loads(result)
        
        self.assertEqual(result_data["total_containers"], 2)
        self.assertEqual(result_data["containers_with_blobs"], 1)
        self.assertEqual(result_data["empty_containers"], 1)
        self.assertEqual(result_data["error_containers"], 0)


class TestDownloadBlobTool(unittest.TestCase):
    """Test the download_blob MCP tool."""

    @patch('server.generate_blob_sas', return_value='fake-sas-token')
    @patch('server.create_blob_service_client')
    @patch('server.get_storage_config')
    def test_download_blob_success(self, mock_get_config, mock_create_client, mock_gen_sas):
        """Test successful blob download URL generation."""
        mock_get_config.return_value = {
            "containers": [
                {
                    "container_name": "test-container",
                    "account_name": "testaccount",
                    "account_key": "testkey123"
                }
            ]
        }

        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client.exists.return_value = True
        mock_blob_client.exists.return_value = True

        mock_blob_props = MagicMock()
        mock_blob_props.size = 1024
        mock_blob_props.content_settings.content_type = "text/plain"
        mock_blob_props.last_modified = None
        mock_blob_client.get_blob_properties.return_value = mock_blob_props

        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_create_client.return_value = mock_blob_service

        result = download_blob("test-container", "myfile.txt", 30)
        result_data = json.loads(result)

        self.assertEqual(result_data["container_name"], "test-container")
        self.assertEqual(result_data["blob_name"], "myfile.txt")
        self.assertIn("download_url", result_data)
        self.assertIn("fake-sas-token", result_data["download_url"])
        self.assertEqual(result_data["size"], 1024)
        self.assertEqual(result_data["expiry_minutes"], 30)

    @patch('server.generate_blob_sas', return_value='fake-sas-token')
    @patch('server.create_blob_service_client')
    @patch('server.get_storage_config')
    def test_download_blob_url_encodes_blob_name(self, mock_get_config, mock_create_client, mock_gen_sas):
        """Test that blob names with special characters are URL-encoded."""
        mock_get_config.return_value = {
            "containers": [
                {
                    "container_name": "test-container",
                    "account_name": "testaccount",
                    "account_key": "testkey123"
                }
            ]
        }

        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client.exists.return_value = True
        mock_blob_client.exists.return_value = True

        mock_blob_props = MagicMock()
        mock_blob_props.size = 512
        mock_blob_props.content_settings.content_type = "text/csv"
        mock_blob_props.last_modified = None
        mock_blob_client.get_blob_properties.return_value = mock_blob_props

        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_create_client.return_value = mock_blob_service

        result = download_blob("test-container", "reports/my file (2).csv", 5)
        result_data = json.loads(result)

        self.assertIn("download_url", result_data)
        # Spaces and parens should be encoded, slashes preserved
        self.assertIn("reports/my%20file%20%282%29.csv", result_data["download_url"])
        self.assertNotIn("reports/my file (2).csv?", result_data["download_url"])

    @patch('server.generate_blob_sas', return_value='fake-sas-token')
    @patch('server.create_blob_service_client')
    @patch('server.get_storage_config')
    def test_download_blob_content_disposition(self, mock_get_config, mock_create_client, mock_gen_sas):
        """Test that SAS is generated with Content-Disposition attachment header."""
        mock_get_config.return_value = {
            "containers": [
                {
                    "container_name": "c",
                    "account_name": "a",
                    "account_key": "k"
                }
            ]
        }

        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client.exists.return_value = True
        mock_blob_client.exists.return_value = True

        mock_blob_props = MagicMock()
        mock_blob_props.size = 100
        mock_blob_props.content_settings.content_type = "application/octet-stream"
        mock_blob_props.last_modified = None
        mock_blob_client.get_blob_properties.return_value = mock_blob_props

        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_create_client.return_value = mock_blob_service

        download_blob("c", "folder/data.bin", 5)

        # Verify generate_blob_sas was called with content_disposition
        mock_gen_sas.assert_called_once()
        call_kwargs = mock_gen_sas.call_args[1]
        self.assertIn("content_disposition", call_kwargs)
        self.assertIn('attachment; filename="data.bin"', call_kwargs["content_disposition"])

    @patch('server.get_storage_config')
    def test_download_blob_container_not_configured(self, mock_get_config):
        """Test download_blob with a container not in the configuration."""
        mock_get_config.return_value = {
            "containers": [
                {"container_name": "other-container", "account_name": "a", "account_key": "k"}
            ]
        }

        result = download_blob("missing-container", "file.txt")
        result_data = json.loads(result)

        self.assertIn("error", result_data)
        self.assertIn("not found in configuration", result_data["error"])

    @patch('server.create_blob_service_client')
    @patch('server.get_storage_config')
    def test_download_blob_blob_not_found(self, mock_get_config, mock_create_client):
        """Test download_blob when the blob does not exist."""
        mock_get_config.return_value = {
            "containers": [
                {"container_name": "test-container", "account_name": "a", "account_key": "k"}
            ]
        }

        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client.exists.return_value = True
        mock_blob_client.exists.return_value = False
        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_create_client.return_value = mock_blob_service

        result = download_blob("test-container", "nonexistent.txt")
        result_data = json.loads(result)

        self.assertIn("error", result_data)
        self.assertIn("does not exist", result_data["error"])

    @patch('server.get_storage_config')
    def test_download_blob_missing_credentials(self, mock_get_config):
        """Test download_blob when credentials cannot be resolved."""
        mock_get_config.return_value = {
            "containers": [
                {"container_name": "test-container"}
            ]
        }

        result = download_blob("test-container", "file.txt")
        result_data = json.loads(result)

        self.assertIn("error", result_data)
        self.assertIn("account_name and account_key are required", result_data["error"])

    @patch('server.generate_blob_sas', return_value='sas')
    @patch('server.create_blob_service_client')
    @patch('server.get_storage_config')
    def test_download_blob_expiry_clamped(self, mock_get_config, mock_create_client, mock_gen_sas):
        """Test that expiry_minutes is clamped to valid range."""
        mock_get_config.return_value = {
            "containers": [
                {"container_name": "c", "account_name": "a", "account_key": "k"}
            ]
        }

        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client.exists.return_value = True
        mock_blob_client.exists.return_value = True
        mock_blob_props = MagicMock()
        mock_blob_props.size = 0
        mock_blob_props.content_settings.content_type = None
        mock_blob_props.last_modified = None
        mock_blob_client.get_blob_properties.return_value = mock_blob_props
        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_create_client.return_value = mock_blob_service

        # Test with value exceeding max
        result = download_blob("c", "file.txt", 9999)
        result_data = json.loads(result)
        self.assertEqual(result_data["expiry_minutes"], 60)

        # Test with value below min
        result = download_blob("c", "file.txt", -5)
        result_data = json.loads(result)
        self.assertEqual(result_data["expiry_minutes"], 1)


if __name__ == "__main__":
    unittest.main()
