from ragservice import RagService


def test_cosine_similarity_identical_vectors_is_close_to_one():
    """Identical vectors should have cosine similarity near 1."""
    service = RagService()

    value = service._cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])

    assert value > 0.999


def test_cosine_similarity_orthogonal_vectors_is_close_to_zero():
    """Orthogonal vectors should have cosine similarity near 0."""
    service = RagService()

    value = service._cosine_similarity([1.0, 0.0], [0.0, 1.0])

    assert abs(value) < 1e-9
