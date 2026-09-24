"""OpenRouter Integration and Agent Orchestration Module.

This module provides the :class:`OpenRouterClient` and helper classes to
communicate with the OpenRouter API for large language model inference,
streaming responses, prompt formatting, and multi-turn agent interactions.
"""

import os
from typing import Any, Dict, List, Optional, Union
import httpx


class Message:
    """Represents a single chat message in a conversation thread.

    Attributes:
        role (str): The role of the message author (e.g., 'system', 'user').
        content (str): The textual content of the message.
        name (Optional[str]): Optional author name or function name.
    """

    def __init__(
        self,
        role: str,
        content: str,
        name: Optional[str] = None,
    ) -> None:
        """Initializes a chat message.

        Args:
            role: Role of the sender ('system', 'user', 'assistant').
            content: Text content of the message.
            name: Optional name identifier.
        """
        self.role: str = role
        self.content: str = content
        self.name: Optional[str] = name


class ModelResponse:
    """Structured response container from OpenRouter completion calls.

    Attributes:
        content (str): The primary generated text response from the model.
        model (str): The model identifier that fulfilled the request.
        raw_response (Dict[str, Any]): Full JSON response dictionary.
        usage (Dict[str, Any]): Token usage metrics for the call.
    """

    def __init__(
        self,
        content: str,
        model: str,
        raw_response: Optional[Dict[str, Any]] = None,
        usage: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initializes a model completion response container.

        Args:
            content: Generated text response.
            model: Model identifier used for inference.
            raw_response: Full raw JSON response dict.
            usage: Token consumption metrics dict.
        """
        self.content: str = content
        self.model: str = model
        self.raw_response: Dict[str, Any] = raw_response or {}
        self.usage: Dict[str, Any] = usage or {}


class OpenRouterClient:
    """Client for querying LLM models through the OpenRouter unified API.

    Handles authentication, payload construction, retry logic, tool
    specifications, and completions.

    Attributes:
        api_key (str): OpenRouter API bearer token.
        default_model (str): Default LLM model identifier.
        base_url (str): OpenRouter API base endpoint URL.
        site_url (Optional[str]): Optional app URL for OpenRouter rankings.
        site_name (Optional[str]): Optional app title for OpenRouter rankings.

    Example:
        >>> client = OpenRouterClient(api_key="sk-or-v1-...")
        >>> response = client.generate_completion(
        ...     messages=[{"role": "user", "content": "Hello, Clara!"}],
        ...     model="openai/gpt-4o"
        ... )
        >>> print(response.content)
    """

    DEFAULT_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL: str = "openai/gpt-4o-mini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        base_url: Optional[str] = None,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        """Initializes the OpenRouter client adapter.

        Args:
            api_key: API key string. If None, reads from environment.
            default_model: Default model identifier.
            base_url: Alternative API endpoint URL.
            site_url: Optional app URL for OpenRouter attribution.
            site_name: Optional app title for OpenRouter attribution.
            timeout: Request timeout duration in seconds. Defaults to 60.0.
        """
        self.api_key: str = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.default_model: str = default_model or os.getenv(
            "DEFAULT_MODEL", self.DEFAULT_MODEL
        )
        base = base_url or os.getenv(
            "OPENROUTER_BASE_URL", self.DEFAULT_BASE_URL
        )
        self.base_url: str = base.rstrip("/")
        self.site_url: Optional[str] = site_url or os.getenv(
            "APP_URL", "https://github.com/Aryan-202/clara-core"
        )
        self.site_name: Optional[str] = site_name or os.getenv(
            "APP_NAME", "Clara Core"
        )
        self.timeout: float = timeout

    def _get_headers(self) -> Dict[str, str]:
        """Builds HTTP request headers including auth and attribution.

        Returns:
            Dict[str, str]: Prepared dictionary of HTTP headers.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name
        return headers

    def _format_messages(
        self, messages: List[Union[Dict[str, Any], Message]]
    ) -> List[Dict[str, Any]]:
        """Normalizes input messages into standard OpenRouter schema.

        Args:
            messages: List of message dicts or :class:`Message` instances.

        Returns:
            List[Dict[str, Any]]: Standardized list of message objects.
        """
        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                entry = {"role": msg.role, "content": msg.content}
                if msg.name:
                    entry["name"] = msg.name
                formatted.append(entry)
            elif isinstance(msg, dict):
                formatted.append(msg)
            else:
                formatted.append({"role": "user", "content": str(msg)})
        return formatted

    def generate_completion(
        self,
        messages: List[Union[Dict[str, Any], Message]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Sends a synchronous chat completion request to OpenRouter.

        Args:
            messages: Sequence of message turns representing history.
            model: Model identifier override.
            temperature: Sampling temperature between 0.0 and 2.0.
            max_tokens: Maximum number of completion tokens to generate.
            tools: Optional tool/function definitions.
            **kwargs: Additional parameters for OpenRouter API.

        Returns:
            ModelResponse: Parsed model response.

        Raises:
            RuntimeError: If the HTTP request fails.
        """
        payload: Dict[str, Any] = {
            "model": model or self.default_model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            **kwargs,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools

        url = f"{self.base_url}/chat/completions"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                url, headers=self._get_headers(), json=payload
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"OpenRouter API error (HTTP {response.status_code}): "
                    f"{response.text}"
                )
            data = response.json()
            choices = data.get("choices", [])
            content = ""
            if choices:
                content = choices[0].get("message", {}).get("content", "")
            return ModelResponse(
                content=content,
                model=data.get("model", payload["model"]),
                raw_response=data,
                usage=data.get("usage", {}),
            )

    async def a_generate_completion(
        self,
        messages: List[Union[Dict[str, Any], Message]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Asynchronously sends a chat completion request to OpenRouter.

        Args:
            messages: Sequence of message turns representing history.
            model: Model identifier override.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            tools: Optional tool definitions.
            **kwargs: Extra parameters for OpenRouter payload.

        Returns:
            ModelResponse: Parsed model response.

        Raises:
            RuntimeError: If the HTTP request fails.
        """
        payload: Dict[str, Any] = {
            "model": model or self.default_model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            **kwargs,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools

        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url, headers=self._get_headers(), json=payload
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"OpenRouter API async error (HTTP {response.status_code}): "
                    f"{response.text}"
                )
            data = response.json()
            choices = data.get("choices", [])
            content = ""
            if choices:
                content = choices[0].get("message", {}).get("content", "")
            return ModelResponse(
                content=content,
                model=data.get("model", payload["model"]),
                raw_response=data,
                usage=data.get("usage", {}),
            )
