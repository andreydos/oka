import httpx

from app.config import settings


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self._base_url = (base_url or settings.ollama_url).rstrip("/")
        self._model = model or settings.ollama_model

    async def generate(self, prompt: str, system: str) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 4096},
        }
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(f"{self._base_url}/api/generate", json=payload)
                response.raise_for_status()
                return response.json()["response"].strip()
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:200] if e.response else str(e)
            raise RuntimeError(f"LLM generation failed: {detail}") from e
        except httpx.HTTPError as e:
            raise RuntimeError(f"LLM service unavailable: {e}") from e

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
