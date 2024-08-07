import pytest
from lorebinders.book_dict import BookDict


@pytest.fixture
def sample_book_dict():
    return BookDict(
        book_file="sample_book.txt",
        title="Sample Book",
        author="John Doe",
        narrator="John Smith",
        character_traits=["Thoughts", "Actions"],
        custom_categories=["Events", "Places"],
        user_folder="user_folder_path",
        txt_file="sample_text.txt"
    )

def test_create_instance_with_all_attributes(sample_book_dict):

    assert sample_book_dict.book_file == "sample_book.txt"
    assert sample_book_dict.title == "Sample Book"
    assert sample_book_dict.author == "John Doe"
    assert sample_book_dict.narrator == "John Smith"
    assert sample_book_dict.character_traits == ["Thoughts", "Actions"]
    assert sample_book_dict.custom_categories == ["Events", "Places"]
    assert sample_book_dict.user_folder == "user_folder_path"
    assert sample_book_dict.txt_file == "sample_text.txt"

def test_set_user_folder(sample_book_dict):
    sample_book_dict.set_user_folder("new_user_folder_path")
    assert sample_book_dict.user_folder == "new_user_folder_path"

def test_set_txt_file(sample_book_dict):
    sample_book_dict.set_txt_file("new_sample_text.txt")
    assert sample_book_dict.txt_file == "new_sample_text.txt"
