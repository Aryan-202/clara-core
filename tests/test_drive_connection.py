"""Unit tests for DriveConnection and Drive operations in clara.connections.google."""

from unittest.mock import MagicMock, patch
from clara.connections.registry import registry
from clara.connections.google.drive import (
    DriveConnection,
    delete_file,
    get_file_metadata,
    list_files,
)


class TestDriveConnection:
    """Test DriveConnection lifecycle and registry integration."""

    def test_drive_registration(self):
        conn_cls = registry.get("drive")
        assert conn_cls == DriveConnection
        instance = registry.get_instance("drive")
        assert isinstance(instance, DriveConnection)

    @patch("clara.connections.google.drive._get_drive_service")
    def test_drive_connect_and_disconnect(self, mock_get_service):
        mock_svc = MagicMock()
        mock_get_service.return_value = mock_svc

        conn = DriveConnection()
        assert not conn.is_connected
        assert conn.service is None

        svc = conn.connect(access_token="fake_drive_token")
        assert conn.is_connected
        assert conn.service == mock_svc
        assert svc == mock_svc

        conn.disconnect()
        assert not conn.is_connected
        assert conn.service is None


class TestDriveCRUDOperations:
    """Test Drive API operation functions."""

    def test_list_files(self):
        mock_svc = MagicMock()
        mock_files = mock_svc.files.return_value
        mock_files.list.return_value.execute.return_value = {
            "files": [
                {
                    "id": "file_123",
                    "name": "Project Proposal.pdf",
                    "mimeType": "application/pdf",
                    "modifiedTime": "2026-09-24T12:00:00Z",
                    "size": "1048576",
                }
            ]
        }

        results = list_files(
            query="mimeType = 'application/pdf'",
            page_size=5,
            service=mock_svc,
        )
        assert len(results) == 1
        assert results[0]["id"] == "file_123"
        assert results[0]["name"] == "Project Proposal.pdf"
        mock_files.list.assert_called_once()

    def test_get_file_metadata(self):
        mock_svc = MagicMock()
        mock_files = mock_svc.files.return_value
        mock_files.get.return_value.execute.return_value = {
            "id": "file_123",
            "name": "Design Spec",
            "mimeType": "application/vnd.google-apps.document",
            "size": "2048",
        }

        meta = get_file_metadata("file_123", service=mock_svc)
        assert meta["id"] == "file_123"
        assert meta["name"] == "Design Spec"
        mock_files.get.assert_called_once()

    def test_delete_file(self):
        mock_svc = MagicMock()
        mock_files = mock_svc.files.return_value
        mock_files.delete.return_value.execute.return_value = {}

        result = delete_file("file_to_del", service=mock_svc)
        assert result["status"] == "deleted"
        assert result["file_id"] == "file_to_del"
        mock_files.delete.assert_called_once_with(fileId="file_to_del")

    def test_drive_connection_delegates_to_crud(self):
        conn = DriveConnection()
        mock_svc = MagicMock()
        conn._service = mock_svc
        conn._is_connected = True

        with patch("clara.connections.google.drive.list_files") as mock_list, \
             patch("clara.connections.google.drive.get_file_metadata") as mock_get, \
             patch("clara.connections.google.drive.delete_file") as mock_del:

            mock_list.return_value = [{"id": "f1"}]
            mock_get.return_value = {"id": "f1", "name": "test.txt"}
            mock_del.return_value = {"status": "deleted"}

            assert conn.list_files(query="name contains 'test'") == [{"id": "f1"}]
            assert conn.get_file_metadata("f1") == {"id": "f1", "name": "test.txt"}
            assert conn.delete_file("f1") == {"status": "deleted"}
