import pytest

from app.processing import chunk_text

@pytest.mark.parametrize("text", ["", "   ", "\n\n\t"])
def test_empty_text_gives_no_chunks(text):
    assert chunk_text(text) == []

def test_short_text_is_one_chunk():
    assert chunk_text("A short note.") == ["A short note."]

def test_chunks_respect_size_limit():
    text= " ".join(["word"] * 500)
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunks) <= 100 for chunk in chunks)

def test_chunks_do_not_split_words():
    text = " ".join(f"word{i}" for i in range(300))
    valid_words = set(text.split())

    for chunk in chunk_text(text, chunk_size=100, overlap=20):
        assert all(word in valid_words for word in chunk.split())

def test_consecutive_chunks_overlap():
    text = " ".join(f"word{i}" for i in range(300))
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    for first, second in zip(chunks, chunks[1:]):
        assert first.split()[-1] in second.split()

def test_text_without_spaces_still_finishes():
    chunks = chunk_text("a" * 1000, chunk_size=100, overlap=20)

    assert "".join(chunks) == "a" * 1000

def test_null_characters_and_whitespace_are_cleaned():
    assert chunk_text("Hello\x00\n\n   World") == ["Hello World"]