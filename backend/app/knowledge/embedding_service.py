import httpx

from app.config import settings
from app.ml_mutex import MLMutex


class EmbeddingService:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self._base_url = (base_url or settings.ollama_url).rstrip("/")
        self._model = model or settings.embedding_model

    async def embed(self, text: str) -> list[float]:
        return await self.embed_query(text)

    async def embed_query(self, text: str) -> list[float]:
        async with MLMutex():
            return await self._embed_raw(f"search_query: {text}")

    async def embed_document(self, text: str) -> list[float]:
        async with MLMutex():
            return await self._embed_raw(f"search_document: {text}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        async with MLMutex():
            for text in texts:
                results.append(await self._embed_raw(f"search_document: {text}"))
        return results

    async def _embed_raw(self, text: str) -> list[float]:
        payload = {"model": self._model, "prompt": text}
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self._base_url}/api/embeddings", json=payload)
            response.raise_for_status()
            return response.json()["embedding"]
