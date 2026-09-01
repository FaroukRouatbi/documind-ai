from app.ingestion.chunking import chunk_document

SAMPLE = """Intro text before any heading.

# Q3 Report

Some opening prose.

## Revenue

Revenue grew this quarter.

## Costs

Costs were flat.
"""


def test_chunk_metadata_is_stamped_on_every_chunk():
    chunks = chunk_document(
        SAMPLE,
        embedding_model="test-model",
        embedding_version="v1",
    )

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.embedding_model == "test-model"
        assert chunk.embedding_version == "v1"
        assert chunk.embedding is None
        assert chunk.parent_index is None
        assert chunk.token_count is not None
        assert chunk.token_count > 0


def test_chunk_index_is_sequential():
    chunks = chunk_document(SAMPLE, embedding_model="m", embedding_version="v")

    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_heading_paths_reflect_document_structure():
    chunks = chunk_document(SAMPLE, embedding_model="m", embedding_version="v")

    paths = {c.heading_path for c in chunks}

    assert None in paths  # pre-heading intro
    assert "Q3 Report" in paths  # under H1
    assert "Q3 Report > Revenue" in paths  # H1 > H2
    assert "Q3 Report > Costs" in paths  # sibling H2 replaces Revenue, not nests
    assert "Q3 Report > Revenue > Costs" not in paths  # would appear if de-nesting broke


def test_small_section_stays_one_chunk():
    doc = "# Title\n\nOne short sentence."
    chunks = chunk_document(doc, embedding_model="m", embedding_version="v", budget=500)

    assert len(chunks) == 1


def test_oversized_section_splits_into_multiple_chunks_each_within_budget():
    # Several sentences under one heading, with a deliberately tiny budget
    # so the section must be split across multiple chunks.
    doc = (
        "# Title\n\n"
        "First sentence here. Second sentence here. "
        "Third sentence here. Fourth sentence here. "
        "Fifth sentence here. Sixth sentence here."
    )
    budget = 10  # tokens — small enough to force splitting

    chunks = chunk_document(doc, embedding_model="m", embedding_version="v", budget=budget)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.token_count is not None
        assert chunk.token_count <= budget


def test_empty_document_produces_no_chunks():
    chunks = chunk_document("", embedding_model="m", embedding_version="v")
    assert chunks == []


def test_whitespace_only_document_produces_no_chunks():
    chunks = chunk_document("   \n\n   \n", embedding_model="m", embedding_version="v")
    assert chunks == []


def test_plain_text_no_headings_produces_chunk_with_no_path():
    chunks = chunk_document(
        "Just some text with no headings.", embedding_model="m", embedding_version="v"
    )

    assert len(chunks) == 1
    assert chunks[0].heading_path is None
    assert chunks[0].content == "Just some text with no headings."
