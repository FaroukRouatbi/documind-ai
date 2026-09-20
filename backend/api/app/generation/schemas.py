import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationResult:
    text: str
    stop_reason: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class BuiltPrompt:
    system: str
    user_content: str
    citation_map: dict[int, uuid.UUID]


@dataclass(frozen=True)
class AnswerResult:
    text: str
    citations: list[uuid.UUID]
    stop_reason: str
    input_tokens: int
    output_tokens: int
