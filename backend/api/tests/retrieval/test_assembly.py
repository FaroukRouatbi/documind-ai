from app.retrieval.assembly import dedup_chunks, reorder_lost_in_middle


def test_reorder_places_most_relevant_at_extremes():
    # input is relevance-sorted: A most relevant, E least
    chunks = ["A", "B", "C", "D", "E"]

    result = reorder_lost_in_middle(chunks)

    assert result == ["A", "C", "E", "D", "B"]
    # A (best) at the front, B (2nd best) at the back, E (worst) in the middle


def test_reorder_empty_list():
    assert reorder_lost_in_middle([]) == []


def test_reorder_single_element():
    assert reorder_lost_in_middle(["A"]) == ["A"]


def test_reorder_two_elements():
    # A at front, B at back (both extremes) — nothing in the middle
    assert reorder_lost_in_middle(["A", "B"]) == ["A", "B"]


def test_dedup_removes_exact_duplicates_preserving_order():
    items = ["A", "B", "A", "C", "B"]
    result = dedup_chunks(items, key=lambda s: s)
    assert result == ["A", "B", "C"]  # first occurrences, in order


def test_dedup_no_duplicates_unchanged():
    items = ["A", "B", "C"]
    assert dedup_chunks(items, key=lambda s: s) == ["A", "B", "C"]


def test_dedup_empty():
    assert dedup_chunks([], key=lambda s: s) == []
