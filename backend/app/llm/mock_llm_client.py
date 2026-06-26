class MockLLMClient:
    async def generate(self, prompt: str, system: str) -> str:
        return "This is a mock answer based on the provided context."

    async def is_available(self) -> bool:
        return True
