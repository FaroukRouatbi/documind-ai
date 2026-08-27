from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkData:
    content: str
    chunk_index: int
    embedding: list[float] | None
    embedding_model: str
    embedding_version: str
    heading_path: str | None
    token_count: int | None
    parent_index: int | None
