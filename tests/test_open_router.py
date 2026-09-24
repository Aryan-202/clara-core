"""Unit tests for OpenRouterClient, Message, and ModelResponse in clara.agent."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from clara.agent.open_router import Message, ModelResponse, OpenRouterClient


class TestMessageAndModelResponse:
    """Test data models for OpenRouter integration."""

    def test_message_creation(self):
        msg = Message(role="user", content="Hello Clara", name="User1")
        assert msg.role == "user"
        assert msg.content == "Hello Clara"
        assert msg.name == "User1"

    def test_model_response_creation(self):
        res = ModelResponse(
            content="Hi there!",
            model="openai/gpt-4o",
            raw_response={"id": "chat-1"},
            usage={"total_tokens": 42},
        )
        assert res.content == "Hi there!"
        assert res.model == "openai/gpt-4o"
        assert res.raw_response == {"id": "chat-1"}
        assert res.usage == {"total_tokens": 42}


class TestOpenRouterClient:
    """Test OpenRouterClient methods and HTTP communication."""

    def test_client_init_defaults(self):
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-env-key"}):
            client = OpenRouterClient()
            assert client.api_key == "test-env-key"
            assert client.default_model == "openai/gpt-4o-mini"
            assert client.base_url == "https://openrouter.ai/api/v1"

    def test_client_init_custom_args(self):
        client = OpenRouterClient(
            api_key="sk-custom",
            default_model="anthropic/claude-3.5-sonnet",
            base_url="https://custom.openrouter.ai/api/v1/",
            site_url="https://myapp.com",
            site_name="My App",
            timeout=30.0,
        )
        assert client.api_key == "sk-custom"
        assert client.default_model == "anthropic/claude-3.5-sonnet"
        assert client.base_url == "https://custom.openrouter.ai/api/v1"
        assert client.site_url == "https://myapp.com"
        assert client.site_name == "My App"
        assert client.timeout == 30.0

    def test_get_headers(self):
        client = OpenRouterClient(
            api_key="test-key",
            site_url="https://clara.ai",
            site_name="Clara",
        )
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["HTTP-Referer"] == "https://clara.ai"
        assert headers["X-Title"] == "Clara"

    def test_format_messages(self):
        client = OpenRouterClient(api_key="test-key")
        raw_msgs = [
            Message(role="system", content="System instruction", name="Admin"),
            {"role": "user", "content": "User question"},
            "Simple string prompt",
        ]
        formatted = client._format_messages(raw_msgs)
        assert len(formatted) == 3
        assert formatted[0] == {
            "role": "system",
            "content": "System instruction",
            "name": "Admin",
        }
        assert formatted[1] == {"role": "user", "content": "User question"}
        assert formatted[2] == {
            "role": "user",
            "content": "Simple string prompt",
        }

    @patch("httpx.Client")
    def test_generate_completion_success(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "model": "openai/gpt-4o",
            "choices": [{"message": {"content": "Generated reply"}}],
            "usage": {"total_tokens": 50},
        }

        mock_http_client = MagicMock()
        mock_http_client.post.return_value = mock_resp
        mock_client_cls.return_value.__enter__.return_value = mock_http_client

        client = OpenRouterClient(api_key="test-key")
        result = client.generate_completion(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            tools=[{"type": "function", "function": {"name": "test_fn"}}],
        )

        assert isinstance(result, ModelResponse)
        assert result.content == "Generated reply"
        assert result.model == "openai/gpt-4o"
        assert result.usage == {"total_tokens": 50}
        mock_http_client.post.assert_called_once()

    @patch("httpx.Client")
    def test_generate_completion_error_raises_runtime_error(
        self, mock_client_cls
    ):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized: Invalid API Key"

        mock_http_client = MagicMock()
        mock_http_client.post.return_value = mock_resp
        mock_client_cls.return_value.__enter__.return_value = mock_http_client

        client = OpenRouterClient(api_key="invalid-key")
        with pytest.raises(RuntimeError, match="OpenRouter API error"):
            client.generate_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_a_generate_completion_success(self, mock_async_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "model": "openai/gpt-4o-mini",
            "choices": [{"message": {"content": "Async generated reply"}}],
            "usage": {"total_tokens": 25},
        }

        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_resp
        mock_async_client_cls.return_value.__aenter__.return_value = (
            mock_http_client
        )

        client = OpenRouterClient(api_key="test-key")
        result = await client.a_generate_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert isinstance(result, ModelResponse)
        assert result.content == "Async generated reply"
        assert result.model == "openai/gpt-4o-mini"
        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_a_generate_completion_error_raises_runtime_error(
        self, mock_async_client_cls
    ):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_resp
        mock_async_client_cls.return_value.__aenter__.return_value = (
            mock_http_client
        )

        client = OpenRouterClient(api_key="test-key")
        with pytest.raises(RuntimeError, match="OpenRouter API async error"):
            await client.a_generate_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )
