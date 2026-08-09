from markdown_it import MarkdownIt

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
    for path, content in parse_into_sections(sample):
        print(f"PATH: {path!r}")
        print(f"CONTENT: {content!r}")
        print("---")