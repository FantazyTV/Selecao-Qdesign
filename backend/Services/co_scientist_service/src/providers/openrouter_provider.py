import asyncio
import json
from typing import AsyncIterator

import httpx

from .base_provider import LLMProvider
from ..config.settings import settings


class OpenRouterProvider(LLMProvider):
    def __init__(self):
        if not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        self._client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            timeout=settings.openrouter_timeout,
        )

    def _headers(self) -> dict:
        headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
        if settings.openrouter_http_referer:
            headers["HTTP-Referer"] = settings.openrouter_http_referer
        if settings.openrouter_app_title:
            headers["X-Title"] = settings.openrouter_app_title
        return headers

    async def generate(self, messages: list[dict]) -> dict:
        payload = {"model": settings.openrouter_model, "messages": messages}
        for attempt in range(3):
            resp = await self._client.post("/chat/completions", headers=self._headers(), json=payload)
            if resp.status_code != 429:
                break
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
        if not resp.is_success:
            return {"error": {"status_code": resp.status_code, "body": resp.text}}
        return resp.json()

    async def stream(self, messages: list[dict]) -> AsyncIterator[str]:
        payload = {"model": settings.openrouter_model, "messages": messages, "stream": True}
        async with self._client.stream(
            "POST", "/chat/completions", headers=self._headers(), json=payload
        ) as resp:
            if not resp.is_success:
                yield json.dumps({"error": {"status_code": resp.status_code, "body": resp.text}})
                return
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line.removeprefix("data: ")
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                delta = chunk["choices"][0].get("delta", {}).get("content")
                if delta:
                    yield delta
