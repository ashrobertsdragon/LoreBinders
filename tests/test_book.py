import pytest

from src.lorebinders.book import Book, Chapter
from src.lorebinders.book_dict import BookDict


@pytest.fixture
def sample_book_dict():
    return BookDict(
        title="Sample Book",
        author="John Doe",
        book_file="sample_book.txt",
        narrator="John Smith",
        character_traits=["Thoughts", "Actions"],
        custom_categories=["Events", "Places"],
    )


@pytest.fixture
def sample_book(sample_book_dict, monkeypatch):
    mock_file_content = "Chapter 1\n***\nChapter 2\n***\nChapter 3"

    def mock_read_text_file(file_path):
        assert file_path == "sample_book.txt"
        return mock_file_content

    monkeypatch.setattr("file_handling.read_text_file", mock_read_text_file)
    return Book(sample_book_dict)


def test_book_init(sample_book_dict, sample_book):
    assert sample_book.title == "Sample Book"
    assert sample_book.author == "John Doe"
    assert sample_book._book_file == "sample_book.txt"
    assert sample_book.narrator == "John Smith"
    assert sample_book.character_attributes == ["Thoughts", "Actions"]
    assert sample_book.custom_categories == ["Events", "Places"]
    assert sample_book.name == "Sample Book"
    assert sample_book.file == "Chapter 1\nChapter 2\nChapter 3"


def test_book_build_chapters(sample_book):
    assert len(sample_book.chapters) == 3
    for chapter in sample_book.chapters:
        assert isinstance(chapter, Chapter)


def test_book_add_binder(sample_book):
    sample_binder = {"Characters": {"John Smith": {"Thoughts": "Thinking"}}}
    sample_book.add_binder(sample_binder)
    assert sample_book.binder == sample_binder


def test_book_update_binder(sample_book):
    sample_binder = {"Characters": {"John Smith": {"Thoughts": "Thinking"}}}
    sample_book.update_binder(sample_binder)
    assert sample_book.binder == sample_binder
    new_binder = {
        "Characters": {
            "John Smith": {"Thoughts": "Thinking", "Actions": "Acting"}
        }
    }
    sample_book.update_binder(new_binder)
    assert sample_book.binder == new_binder


def test_chapter_init(sample_book):
    chapter = sample_book.chapters[0]
    assert isinstance(chapter, Chapter)
    assert chapter.number == 1
    assert chapter.text == "Chapter 1"


def test_chapter_add_analysis(sample_book):
    chapter = sample_book.chapters[0]
    sample_analysis = {
        "Characters": {
            "John Smith": {"Thoughts": "Thinking", "Actions": "Acting"}
        }
    }
    chapter.add_analysis(sample_analysis)
    assert chapter.analysis == sample_analysis


def test_chapter_add_names(sample_book):
    chapter = sample_book.chapters[0]
    sample_names = {
        "Characters": {
            "John Smith": {"Thoughts": "Thinking", "Actions": "Acting"}
        }
    }
    chapter.add_names(sample_names)
    assert chapter.names == sample_names
