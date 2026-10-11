"""Unit tests for Google OAuth token exchange and credentials construction."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from clara.auth.google import exchange_server_auth_code
from clara.connections.google.calendar import _get_calendar_service
from clara.connections.google.drive import _get_drive_service
from clara.connections.google.gmail import GmailConnection, _get_gmail_service
from clara.main import clara

client = TestClient(clara)


class TestExchangeServerAuthCode:
    """Tests for exchange_server_auth_code function."""

    def test_missing_or_empty_code_returns_error(self):
        res1 = exchange_server_auth_code("")
        assert res1["status"] == "error"
        assert res1["error"] == "invalid_request"

        res2 = exchange_server_auth_code("   ")
        assert res2["status"] == "error"

    @patch("urllib.request.urlopen")
    def test_successful_code_exchange(self, mock_urlopen):
        mock_response = io.BytesIO(
            json.dumps({
                "access_token": "ya29.mock_access_token",
                "refresh_token": "1//04_mock_refresh_token",
                "expires_in": 3599,
                "token_type": "Bearer",
                "scope": "https://www.googleapis.com/auth/gmail.modify",
            }).encode("utf-8")
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = lambda s, *args: None
        mock_urlopen.return_value = mock_response

        res = exchange_server_auth_code(
            server_auth_code="4/0AWtgzhMockAuthCode",
            client_id="mock_client_id.apps.googleusercontent.com",
            client_secret="mock_secret",
            redirect_uri="",
        )

        assert res["status"] == "success"
        assert res["access_token"] == "ya29.mock_access_token"
        assert res["refresh_token"] == "1//04_mock_refresh_token"
        assert res["expires_in"] == 3599
        assert res["token_type"] == "Bearer"

    @patch("urllib.request.urlopen")
    def test_http_error_during_exchange(self, mock_urlopen):
        err_body = io.BytesIO(
            json.dumps({
                "error": "invalid_grant",
                "error_description": "Bad Request",
            }).encode("utf-8")
        )
        http_err = urllib.error.HTTPError(
            url="https://oauth2.googleapis.com/token",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=err_body,
        )
        mock_urlopen.side_effect = http_err

        res = exchange_server_auth_code(
            server_auth_code="invalid_code",
        )

        assert res["status"] == "error"
        assert res["error"] == "invalid_grant"
        assert "Bad Request" in res["error_description"]

    @patch("urllib.request.urlopen")
    def test_network_exception_during_exchange(self, mock_urlopen):
        mock_urlopen.side_effect = ConnectionResetError("Connection reset")

        res = exchange_server_auth_code("code123")
        assert res["status"] == "error"
        assert res["error"] == "request_failed"


class TestAuthExchangeEndpoints:
    """Tests for POST /api/auth/google/exchange and /api/auth/exchange."""

    @patch("clara.auth.google.exchange_server_auth_code")
    def test_exchange_endpoint_success_snake_case(self, mock_exchange):
        mock_exchange.return_value = {
            "status": "success",
            "access_token": "ya29.token",
            "refresh_token": "1//refresh",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        resp = client.post(
            "/api/auth/google/exchange",
            json={"server_auth_code": "4/mock_code"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["access_token"] == "ya29.token"
        mock_exchange.assert_called_once_with(
            server_auth_code="4/mock_code",
            client_id=None,
            client_secret=None,
            redirect_uri="",
        )

    @patch("clara.auth.google.exchange_server_auth_code")
    def test_exchange_endpoint_success_camel_case(self, mock_exchange):
        mock_exchange.return_value = {
            "status": "success",
            "access_token": "ya29.token",
            "refresh_token": "1//refresh",
        }

        resp = client.post(
            "/api/auth/exchange",
            json={
                "serverAuthCode": "4/mock_code_camel",
                "clientId": "web_id",
                "clientSecret": "web_sec",
            },
        )
        assert resp.status_code == 200
        mock_exchange.assert_called_once_with(
            server_auth_code="4/mock_code_camel",
            client_id="web_id",
            client_secret="web_sec",
            redirect_uri="",
        )

    def test_exchange_endpoint_missing_code_returns_400(self):
        resp = client.post(
            "/api/auth/google/exchange",
            json={"client_id": "only_client_id"},
        )
        assert resp.status_code == 400
        assert "server_auth_code" in resp.json()["detail"]

    @patch("clara.auth.google.exchange_server_auth_code")
    def test_exchange_endpoint_failure_returns_400(self, mock_exchange):
        mock_exchange.return_value = {
            "status": "error",
            "error": "invalid_grant",
            "error_description": "Code expired",
        }

        resp = client.post(
            "/api/auth/google/exchange",
            json={"server_auth_code": "expired_code"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"] == "invalid_grant"


class TestGoogleCredentialsConstruction:
    """Tests verifying Credentials construction and avoiding unnecessary refresh."""

    @patch("clara.connections.google.gmail.build")
    @patch("clara.connections.google.gmail.Credentials")
    def test_gmail_credentials_populated_with_offline_fields(
        self, mock_creds_cls, mock_build
    ):
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = True
        mock_creds_cls.return_value = mock_creds_instance

        _get_gmail_service(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

        mock_creds_cls.assert_called_once()
        _, kwargs = mock_creds_cls.call_args
        assert kwargs["token"] == "test_access_token"
        assert kwargs["refresh_token"] == "test_refresh_token"
        assert kwargs["client_id"] == "test_client_id"
        assert kwargs["client_secret"] == "test_client_secret"
        assert "oauth2.googleapis.com" in kwargs["token_uri"]

        # Valid credentials must not invoke refresh
        mock_creds_instance.refresh.assert_not_called()
        mock_build.assert_called_once_with(
            "gmail", "v1", credentials=mock_creds_instance
        )

    @patch("clara.connections.google.gmail.build")
    @patch("clara.connections.google.gmail.Credentials")
    def test_gmail_credentials_does_not_refresh_when_refresh_token_is_none(
        self, mock_creds_cls, mock_build
    ):
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = True
        mock_creds_instance.refresh_token = None
        mock_creds_cls.return_value = mock_creds_instance

        _get_gmail_service(access_token="valid_access_token")

        mock_creds_instance.refresh.assert_not_called()
        mock_build.assert_called_once()

    @patch("clara.connections.google.calendar.build")
    @patch("clara.connections.google.calendar.Credentials")
    def test_calendar_credentials_construction(
        self, mock_creds_cls, mock_build
    ):
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = True
        mock_creds_cls.return_value = mock_creds_instance

        _get_calendar_service(
            access_token="cal_token",
            refresh_token="cal_refresh",
            client_id="cal_client_id",
        )

        mock_creds_cls.assert_called_once()
        _, kwargs = mock_creds_cls.call_args
        assert kwargs["token"] == "cal_token"
        assert kwargs["refresh_token"] == "cal_refresh"
        assert kwargs["client_id"] == "cal_client_id"
        mock_creds_instance.refresh.assert_not_called()

    @patch("clara.connections.google.drive.build")
    @patch("clara.connections.google.drive.Credentials")
    def test_drive_credentials_construction(
        self, mock_creds_cls, mock_build
    ):
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = True
        mock_creds_cls.return_value = mock_creds_instance

        _get_drive_service(
            access_token="drive_token",
            refresh_token="drive_refresh",
            client_secret="drive_secret",
        )

        mock_creds_cls.assert_called_once()
        _, kwargs = mock_creds_cls.call_args
        assert kwargs["token"] == "drive_token"
        assert kwargs["refresh_token"] == "drive_refresh"
        assert kwargs["client_secret"] == "drive_secret"
        mock_creds_instance.refresh.assert_not_called()

    @patch("clara.connections.google.gmail._get_gmail_service")
    def test_gmail_connection_passes_refresh_token(self, mock_get_svc):
        conn = GmailConnection()
        conn.connect(
            access_token="acc_tok",
            refresh_token="ref_tok",
            client_id="my_client",
        )
        mock_get_svc.assert_called_once()
        _, kwargs = mock_get_svc.call_args
        assert kwargs["access_token"] == "acc_tok"
        assert kwargs["refresh_token"] == "ref_tok"
        assert kwargs["client_id"] == "my_client"
