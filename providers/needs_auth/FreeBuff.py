from __future__ import annotations

import json
import os
from ..template import OpenaiTemplate
from ...cookies import read_cookie_files, get_cookies_dir
from ... import debug


class FreeBuff(OpenaiTemplate):
    label = "FreeBuff"
    url = "https://freebuff.com"
    working = True
    needs_auth = True
    models_needs_auth = True
    base_url = "https://freebuff.com/api/v1"
    default_model = "freebuff-default"
    sort_models = False

    # Cookie names from freebuff HAR
    COOKIE_NAMES = [
        "__Secure-next-auth.session-token",
        "__Host-next-auth.csrf-token",
        "__Secure-next-auth.callback-url",
        "last_provider",
        "human_behavior_end_user_id",
        "vly_device_id",
    ]

    @classmethod
    def get_models(cls, api_key: str = None, **kwargs) -> list[str]:
        """Fetch available models from FreeBuff."""
        if cls.models:
            return cls.models

        # Try to load cookies from HAR/JSON files in cookies directory
        cookies_dir = get_cookies_dir()
        freebuff_har = os.path.join(cookies_dir, "freebuff.har")
        if os.path.exists(freebuff_har):
            try:
                read_cookie_files(dir_path=cookies_dir, domains_filter=["freebuff.com"])
                debug.log("Loaded FreeBuff cookies from HAR file")
            except Exception as e:
                debug.error(f"Failed to load FreeBuff cookies: {e}")

        # Fallback models if API not accessible
        cls.fallback_models = [
            "freebuff-default",
            "freebuff-pro",
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-sonnet",
            "claude-3-haiku",
        ]
        cls.models = cls.fallback_models.copy()
        return cls.models

    @classmethod
    def get_headers(cls, stream: bool, api_key: str = None, headers: dict = None) -> dict:
        """Build headers with FreeBuff authentication cookies."""
        cookie_dict = {}
        cookies_dir = get_cookies_dir()

        # Try to load from HAR file first
        freebuff_har = os.path.join(cookies_dir, "freebuff.har")
        if os.path.exists(freebuff_har):
            try:
                with open(freebuff_har, 'r') as f:
                    har_data = json.load(f)
                for entry in har_data.get('log', {}).get('entries', []):
                    req_cookies = entry.get('request', {}).get('cookies', [])
                    for c in req_cookies:
                        if c['name'] in cls.COOKIE_NAMES:
                            cookie_dict[c['name']] = c['value']
            except Exception as e:
                debug.error(f"Failed to parse FreeBuff HAR: {e}")

        # Build cookie header
        cookie_header = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()]) if cookie_dict else ""

        return {
            "Accept": "text/event-stream" if stream else "application/json",
            "Content-Type": "application/json",
            "Origin": "https://freebuff.com",
            "Referer": "https://freebuff.com/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            **({"Cookie": cookie_header} if cookie_header else {}),
            **(headers or {}),
        }

    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        conversation: JsonConversation = None,
        media: MediaListType = None,
        api_key: str = None,
        api_endpoint: str = None,
        base_url: str = None,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = None,
        stop: Union[str, list[str]] = None,
        stream: bool = None,
        prompt: str = None,
        user: str = None,
        headers: dict = None,
        impersonate: str = None,
        download_media: bool = True,
        extra_parameters: list[str] = [
            "tools",
            "parallel_tool_calls",
            "tool_choice",
            "reasoning_effort",
            "logit_bias",
            "modalities",
            "audio",
            "stream_options",
            "include_reasoning",
            "response_format",
            "max_completion_tokens",
            "reasoning_effort",
            "search_settings",
            "prompt_cache_key",
        ],
        extra_body: dict = None,
        yield_request: bool = True,
        **kwargs,
    ) -> AsyncResult:
        # Use the parent implementation but with FreeBuff specific headers
        return await super().create_async_generator(
            model=model,
            messages=messages,
            proxy=proxy,
            conversation=conversation,
            media=media,
            api_key=api_key,
            api_endpoint=api_endpoint,
            base_url=base_url or cls.base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
            stream=stream,
            prompt=prompt,
            user=user,
            headers=cls.get_headers(stream or True, api_key, headers),
            impersonate=impersonate or "chrome",
            download_media=download_media,
            extra_parameters=extra_parameters,
            extra_body=extra_body,
            yield_request=yield_request,
            **kwargs,
        )