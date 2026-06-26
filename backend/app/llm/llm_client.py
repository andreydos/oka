from typing import Protocol


class LLMClient(Protocol):
    async def generate(self, prompt: str, system: str) -> str:
        """Generate a completion from the local LLM."""

    async def is_available(self) -> bool:
        """Check if the LLM runtime is reachable."""
