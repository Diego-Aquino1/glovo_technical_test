from typing import Any

import httpx

from app.config import settings


class ERPClient:
    _client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.erp_service_url,
            timeout=30.0,
            follow_redirects=True,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("ERPClient no inicializado. Llama a initialize() primero.")
        return self._client

    async def get_article(self, sku: str) -> dict[str, Any] | None:
        client = self._ensure_client()
        response = await client.get(f"/articles/{sku}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def get_all_pages(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        client = self._ensure_client()
        all_items: list[dict[str, Any]] = []
        page = 1
        page_size = 100

        while True:
            response = await client.get(
                path,
                params={**params, "page": page, "size": page_size},
            )
            response.raise_for_status()
            data = response.json()

            items: list = data.get("items", [])
            all_items.extend(items)

            total_pages: int = data.get("pages", 1)
            if page >= total_pages or not items:
                break
            page += 1

        return all_items


erp_client = ERPClient()
