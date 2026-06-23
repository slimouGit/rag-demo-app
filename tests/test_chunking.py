from ragservice import RagService


def test_split_into_chunks_returns_chunks_for_non_empty_text():
    """Chunking should return at least one chunk for non-empty input."""
    service = RagService()
    text = "A" * 2500

    chunks = service._split_into_chunks(text)

    assert chunks
    assert all(chunk.strip() for chunk in chunks)


def test_ingest_text_raises_for_empty_content():
    """Ingest should reject empty or whitespace-only text."""
    service = RagService()

    try:
        service._ingest_text("empty-doc", "   \n\t  ")
        assert False, "Expected ValueError for empty content"
    except ValueError as exc:
        assert "lesbaren Text" in str(exc)
