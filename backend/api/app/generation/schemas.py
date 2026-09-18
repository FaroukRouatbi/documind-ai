from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationResult:
    text: str
    stop_reason: str
    input_tokens: int
    output_tokens: int
