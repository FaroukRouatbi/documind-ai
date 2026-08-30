from typing import Protocol


class Embedder(Protocol):
    model_id: str
    embedding_version: str

    async def embed(self, text: str) -> list[float]: ...
