from unittest.mock import patch
import pytest

from lorebinders.book import Book, Chapter
from lorebinders.book_dict import BookDict


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
def mock_read_text_file():
    return "Chapter 1\n***\nChapter 2\n***\nChapter 3"

@pytest.fixture
def mock_chapter():
    return Chapter(1, "Sample text")


@pytest.fixture
def mock_build_chapters(mock_chapter):
    return list(mock_chapter * 3)


@pytest.fixture
def sample_book(sample_book_dict, mock_read_text_file):
    with patch("lorebinders.book.read_text_file", return_value=mock_read_text_file):
        return Book(sample_book_dict)


@patch.object(Book, "_build_chapters")
def test_book_init(mock_build_chapters, sample_book_dict):
    with patch("lorebinders.book.read_text_file", return_value="Chapter 1\n***\nChapter 2\n***\nChapter 3"):
        book = Book(sample_book_dict)
        assert book.title == "Sample Book"
        assert book.author == "John Doe"
        assert book._book_file == "sample_book.txt"
        assert book.narrator == "John Smith"
        assert book.character_attributes == ["Thoughts", "Actions"]
        assert book.custom_categories == ["Events", "Places"]
        assert book.name == "Sample Book"
        assert book.file == "Chapter 1\n***\nChapter 2\n***\nChapter 3"
        mock_build_chapters.assert_called_once()

def test_book_repr(sample_book):
    assert repr(sample_book) == "Book('Sample Book')"

def test_book_build_chapters(sample_book, mock_read_text_file):
    sample_book.file = mock_read_text_file
    sample_book._build_chapters()
    assert len(sample_book._chapters) == 3
    assert len(sample_book.chapters) == 3


def test_chapter_init(mock_chapter):
    assert isinstance(mock_chapter, Chapter)
    assert mock_chapter.number == 1
    assert mock_chapter.text == "Sample text"


def test_chapter_add_analysis(mock_chapter):
    sample_analysis = {
        "Characters": {
            "John Smith": {"Thoughts": "Thinking", "Actions": "Acting"}
        }
    }
    mock_chapter.add_analysis(sample_analysis)
    assert mock_chapter.analysis == sample_analysis


def test_chapter_add_names(mock_chapter):
    sample_names = {
        "Characters": {
            "John Smith": {"Thoughts": "Thinking", "Actions": "Acting"}
        }
    }
    mock_chapter.add_names(sample_names)
    assert mock_chapter.names == sample_names


def test_chapter_add_names_invalid_type(mock_chapter):

    with pytest.raises(TypeError, match="Names must be a dictionary"):
        mock_chapter.add_names(["Not", "a", "dict"])

def test_chapter_add_analysis_invalid_type(mock_chapter):
    with pytest.raises(TypeError, match="Analysis must be a dictionary"):
        mock_chapter.add_analysis(["Not", "a", "dict"])


def test_add_valid_binder_dictionary(sample_book):
    binder = {"key": "value"}
    sample_book.add_binder(binder)
    assert sample_book.binder == binder


def test_ensure_binder_assigned_correctly(sample_book):
    binder = {"key": "value"}
    sample_book.add_binder(binder)
    assert sample_book._binder == binder

def test_add_binder_valid_dictionary(sample_book):
    valid_binder = {"key": "value"}
    assert sample_book.add_binder(valid_binder) is None


def test_update_binder_when_different(sample_book):
    binder = {"key1": "value1", "key2": "value2"}
    new_binder = {"key1": "new_value1", "key2": "value2"}

    sample_book.add_binder(binder)
    sample_book.update_binder(new_binder)

    assert sample_book._binder == new_binder

def test_update_binder_does_not_change_binder_when_not_different(sample_book):
    binder = {"key": "value"}
    sample_book.add_binder(binder)
    assert sample_book._binder == binder

    sample_book.update_binder(binder)
    assert sample_book._binder == binder

    different_binder = {"another_key": "another_value"}
    sample_book.update_binder(different_binder)
    assert sample_book._binder == different_binder


def test_update_binder_no_errors_for_valid_dict(sample_book):
    valid_dict = {"key": "value"}
    assert sample_book.update_binder(valid_dict) is None


def test_retrieving_binder_dictionary(sample_book):
    binder_dict = {"key": "value"}
    sample_book.add_binder(binder_dict)
    assert sample_book.binder == binder_dict


def test_add_binder_non_dictionary_binder_raises_type_error(sample_book):
    with pytest.raises(TypeError, match="Binder must be a dictionary"):
        sample_book.add_binder("Not a dictionary")

def test_update_binder_non_dictionary_binder_raises_type_error(sample_book):
    with pytest.raises(TypeError, match="Binder must be a dictionary"):
        sample_book.update_binder("Not a dictionary")
