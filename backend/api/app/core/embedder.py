from typing import Protocol


class Embedder(Protocol):
    @property
    def model_id(self) -> str: ...

    @property
    def embedding_version(self) -> str: ...

    async def embed(self, text: str) -> list[float]: ...
