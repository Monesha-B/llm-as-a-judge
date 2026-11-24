import pytest
from llm_judge.reference import extract_reference, MAX_BYTES, MAX_CHARS


def test_txt():
    assert extract_reference("a.txt", b"  policy one  ") == "policy one"


def test_markdown():
    assert extract_reference("info.md", "caf\u00e9".encode()) == "caf\u00e9"


def test_bom():
    assert extract_reference("data.TXT", b"\xef\xbb\xbfhello") == "hello"


def test_invalid_extension():
    with pytest.raises(ValueError):
        extract_reference("f.exe", b"hello")


def test_empty():
    with pytest.raises(ValueError):
        extract_reference("f.txt", b"")


def test_large_file():
    with pytest.raises(ValueError):
        extract_reference("f.txt", b"a" * (MAX_BYTES+1))


def test_invalid_utf8():
    with pytest.raises(ValueError):
        extract_reference("f.txt", b"\xff\xff")


def test_truncate():
    assert len(extract_reference("f.md", b"a" * (MAX_CHARS+100))) == MAX_CHARS


def test_empty_text():
    with pytest.raises(ValueError):
        extract_reference("f.md", b"   ")
