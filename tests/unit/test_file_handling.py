import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


from lorebinders.file_handling import (
    separate_into_chapters,
    append_json_file,
    read_json_file,
    read_text_file,
    write_json_file,
    write_to_file,
)

@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        temp_file_path = Path(tmp.name)
    yield temp_file_path
    temp_file_path.unlink()


def test_append_json_file_new_file(temp_file):
    temp_file.unlink()
    content = [1, 2, 3]
    append_json_file(content, temp_file)
    with temp_file.open() as f:
        assert json.load(f) == content


def test_append_json_file_existing_file_list(temp_file):
    initial_content = [1, 2]
    json.dump(initial_content, temp_file.open("w"))
    new_content = [3, 4]
    append_json_file(new_content, temp_file)
    with temp_file.open() as f:
        assert json.load(f) == initial_content + new_content


def test_append_json_file_existing_file_dict(temp_file):
    initial_content = {"a": 1, "b": 2}
    json.dump(initial_content, temp_file.open("w"))
    new_content = {"c": 3, "d": 4}
    append_json_file(new_content, temp_file)
    with temp_file.open() as f:
        assert json.load(f) == {"a": 1, "b": 2, "c": 3, "d": 4}


def test_append_json_file_type_mismatch_error(temp_file):
    initial_content = [1, 2]
    json.dump(initial_content, temp_file.open("w"))
    new_content = {"a": 1}
    with pytest.raises(TypeError):
        append_json_file(new_content, temp_file)


def test_append_json_file_io_error(temp_file):
    content = [1, 2, 3]
    with patch("pathlib.Path.open", side_effect=OSError):
        with pytest.raises(OSError):
            append_json_file(content, temp_file)


def test_separate_into_chapters_single_chapter():
    text = "This is a single chapter."
    result = separate_into_chapters(text)
    assert result == ["This is a single chapter."]


def test_separate_into_chapters_multiple_chapters():
    text = "Chapter 1 ***Chapter 2 ***Chapter 3"
    result = separate_into_chapters(text)
    assert result == ["Chapter 1", "Chapter 2", "Chapter 3"]


def test_separate_into_chapters_leading_trailing_whitespace():
    text = "  ***Chapter 1***   Chapter 2  ***"
    result = separate_into_chapters(text)
    assert result == ["", "Chapter 1", "Chapter 2", ""]


def test_separate_into_chapters_empty_string():
    text = ""
    result = separate_into_chapters(text)
    assert result == [""]


def test_separate_into_chapters_no_chapters():
    text = "This is a single paragraph."
    result = separate_into_chapters(text)
    assert result == ["This is a single paragraph."]


def test_read_text_file(temp_file):
    content = "Hello, World!"
    with temp_file.open("w") as f:
        f.write(content)
    assert read_text_file(temp_file) == content


def test_read_json_file_list(temp_file):
    content = [1, 2, 3]
    with temp_file.open("w") as f:
        json.dump(content, f)
    assert read_json_file(temp_file) == content


def test_read_json_file_dict(temp_file):
    content = {"a": 1, "b": 2}
    with temp_file.open("w") as f:
        json.dump(content, f)
    assert read_json_file(temp_file) == content


def test_write_to_file(temp_file):
    content1 = "Hello, World!"
    content2 = "This is a test."
    write_to_file(content1, temp_file)
    write_to_file(content2, temp_file)
    with temp_file.open() as f:
        lines = f.readlines()
    assert lines == ["Hello, World!\n", "This is a test.\n"]


def test_write_json_file_list(temp_file):
    content = [1, 2, 3]
    write_json_file(content, temp_file)
    with temp_file.open() as f:
        assert json.load(f) == content


def test_write_json_file_dict(temp_file):
    content = {"a": 1, "b": 2}
    write_json_file(content, temp_file)
    with temp_file.open() as f:
        assert json.load(f) == content


def test_read_text_file_io_error(temp_file):
    with patch("lorebinders.file_handling.Path.read_text", side_effect=OSError):
        with pytest.raises(OSError):
            read_text_file(temp_file)


def test_read_json_file_io_error(temp_file):
    with patch("pathlib.Path.open", side_effect=OSError):
        with pytest.raises(OSError):
            read_json_file(temp_file)


def test_write_to_file_io_error(temp_file):
    with patch("pathlib.Path.open", side_effect=OSError):
        with pytest.raises(OSError):
            write_to_file("test", temp_file)


@pytest.mark.parametrize("error", [OSError])
@patch("pathlib.Path.open", side_effect=OSError)
def test_write_json_file_io_error(mock_open, temp_file, error):
    with pytest.raises(error):
        write_json_file([1, 2, 3], temp_file)
