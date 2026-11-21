from app.flashcards import sample_evenly
from app.models import Message
from app.rag import build_history, find_citations

def test_find_citations_collects_unique_numbers():
    assert find_citations("Cells divide [1] in phases [2][1].") == {1, 2}

def test_find_citations_with_no_citations():
    assert find_citations("No cited here.") == set()

def test_build_history_skips_unanswered_questions():
    messages = [
        Message(role ="user", content="Q1"),
        Message(role ="assistant", content="A1"),
        Message(role ="user", content="Q2 which failed"),
        Message(role ="user", content="Q3"),
        Message(role ="assistant", content="A3"),
    ]

    assert build_history(messages) == [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q3"},
        {"role": "assistant", "content": "A3"},
    ]

def test_sample_evenly_spreads_across_the_list():
    assert sample_evenly(list(range(100)), 5) == [0, 20, 40, 60, 80]

def test_sample_evenly_keeps_short_lists():
    assert sample_evenly([1, 2, 3], 10) == [1, 2, 3]