from markdown_it import MarkdownIt

import pysbd
import tiktoken

encoder = tiktoken.get_encoding("cl100k_base")

segmenter = pysbd.Segmenter(language="en", clean=False)

md = MarkdownIt()

def parse_into_sections(markdown: str) -> list[tuple[str | None, str]]:
    lines = markdown.split("\n")
    tokens = md.parse(markdown)
    sections = []
    stack = []
    content_start = 0
    current_path = None

    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            heading  = tokens[i+1].content
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

    final_lines = lines[content_start : ]
    content = "\n".join(final_lines).strip()
    if content:
        sections.append((current_path, content))

    return sections

def count_tokens(text: str) -> int:
    return len(encoder.encode(text))

def pack(units: list[str], budget: int, split_further, joiner: str) -> list[str]:
    chunks = []
    current = []
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


if __name__ == "__main__":
    one_big_para = "This is a sentence. " * 200   # one paragraph, no blank lines, way over budget
    result = split_section(one_big_para)
    print(f"{len(result)} chunks, sizes: {[count_tokens(c) for c in result]}")