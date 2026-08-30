import pysbd
import tiktoken
from markdown_it import MarkdownIt

from app.ingestion.schemas import ChunkData

encoder = tiktoken.get_encoding("cl100k_base")

segmenter = pysbd.Segmenter(language="en", clean=False)

md = MarkdownIt()


def parse_into_sections(markdown: str) -> list[tuple[str | None, str]]:
    lines = markdown.split("\n")
    tokens = md.parse(markdown)
    sections: list[tuple[str | None, str]] = []
    stack: list[str] = []
    content_start = 0
    current_path = None

    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            heading = tokens[i + 1].content
            assert token.map is not None
            section_lines = lines[content_start : token.map[0]]
            content = "\n".join(section_lines).strip()
            if content:
                sections.append((current_path, content))
            level = int(token.tag[1])
            while len(stack) >= level:
                stack.pop()

            stack.append(heading)
            content_start = token.map[1]
            current_path = " > ".join(stack)

    final_lines = lines[content_start:]
    content = "\n".join(final_lines).strip()
    if content:
        sections.append((current_path, content))

    return sections


def count_tokens(text: str) -> int:
    return len(encoder.encode(text))


def pack(units: list[str], budget: int, split_further, joiner: str) -> list[str]:
    chunks = []
    current: list[str] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = count_tokens(unit)

        if unit_tokens > budget:
            if current:
                chunks.append(joiner.join(current))
                current = []
                current_tokens = 0
            chunks.extend(split_further(unit))
            continue

        if current_tokens + unit_tokens > budget:
            chunks.append(joiner.join(current))
            current = [unit]
            current_tokens = unit_tokens
        else:
            current.append(unit)
            current_tokens += unit_tokens

    if current:
        chunks.append(joiner.join(current))

    return chunks


def split_into_sentences(text: str, budget: int = 500) -> list[str]:
    sentences = segmenter.segment(text)

    return pack(sentences, budget, lambda s: [s], joiner=" ")


def split_section(content: str, budget: int = 500) -> list[str]:
    if count_tokens(content) <= budget:
        return [content]

    paragraphs = content.split("\n\n")
    return pack(paragraphs, budget, lambda p: split_into_sentences(p, budget), joiner="\n\n")


def chunk_document(
    markdown: str, *, embedding_model: str, embedding_version: str, budget: int = 500
) -> list[ChunkData]:
    sections = parse_into_sections(markdown)
    chunk_index = 0
    chunks = []

    for heading_path, content in sections:
        pieces = split_section(content, budget)

        for piece in pieces:
            chunk = ChunkData(
                content=piece,
                chunk_index=chunk_index,
                embedding=None,
                embedding_model=embedding_model,
                embedding_version=embedding_version,
                heading_path=heading_path,
                token_count=count_tokens(piece),
                parent_index=None,
            )
            chunks.append(chunk)
            chunk_index += 1

    return chunks


if __name__ == "__main__":
    sample = """Intro text before any heading.

# Q3 Report

Some opening prose.

## Revenue

Revenue grew this quarter.

### EMEA

| Region | Growth |
|--------|--------|
| France | 12%    |

## Costs

Costs were flat.
"""
    chunks = chunk_document(
        sample,
        embedding_model="amazon.titan-embed-text-v2:0",
        embedding_version="1",
    )
    for c in chunks:
        print(
            f"[{c.chunk_index}] path={c.heading_path!r} tokens={c.token_count} embedding={c.embedding}" # noqa: E501
        )
        print(f"    content={c.content[:50]!r}")
