from typing import Any, Generator
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lorebinders.prompt_generator import filter_chapters, split_value, add_to_traits, process_chapter_details, iterate_categories, create_description, generate_prompts, create_prompts

@pytest.fixture
def mock_split_value() -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch("lorebinders.prompt_generator.split_value") as mock:
        mock.side_effect= lambda value: [value]
        yield mock

@pytest.fixture
def mock_add_to_traits() -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch("lorebinders.prompt_generator.add_to_traits") as mock:
        mock.side_effect = lambda attribute, value, traits: traits.setdefault(attribute, []).extend(value if isinstance(value, list) else [value]) or traits
        yield mock

@pytest.fixture
def mock_process_chapter_details() -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch("lorebinders.prompt_generator.process_chapter_details") as mock:
        mock.side_effect = lambda chapter_details, traits: {
            **traits,
            **{k: traits.get(k, []) + (v if isinstance(v, list) else [v]) for k, v in chapter_details.items()}
        }
        yield mock

@pytest.fixture
def mock_iterate_categories() -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch("lorebinders.prompt_generator.iterate_categories") as mock:
        yield mock

@pytest.fixture
def mock_filter_chapters() -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch("lorebinders.prompt_generator.filter_chapters") as mock:
        yield mock

@pytest.fixture
def mock_create_description() -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch("lorebinders.prompt_generator.create_description") as mock:
        yield mock

@pytest.fixture
def mock_generate_prompts() -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch("lorebinders.prompt_generator.generate_prompts") as mock:
        yield mock

def test_filter_chapters():
    category_names = {
        "Category1": {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}, "Chapter4": {}},
        "Category2": {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}},
        "Category3": {"Chapter1": {}, "Chapter2": {}}
    }
    expected_output = [("Category1", {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}, "Chapter4": {}})]

    result = list(filter_chapters(category_names))
    assert result == expected_output

def test_filter_chapters_empty_dict():
    category_names = {}
    expected_output = []

    result = list(filter_chapters(category_names))
    assert result == expected_output

def test_filter_chapters_all_below_threshold():
    category_names = {
        "Category1": {"Chapter1": {}, "Chapter2": {}},
        "Category2": {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}},
        "Category3": {"Chapter1": {}, "Chapter2": {}}
    }
    expected_output = []

    result = list(filter_chapters(category_names))
    assert result == expected_output

def test_filter_chapters_all_above_threshold():
    category_names = {
        "Category1": {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}, "Chapter4": {}},
        "Category2": {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}, "Chapter4": {}},
        "Category3": {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}, "Chapter4": {}}
    }
    expected_output = [
        ("Category1", {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}, "Chapter4": {}}),
        ("Category2", {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}, "Chapter4": {}}),
        ("Category3", {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}, "Chapter4": {}})
    ]

    result = list(filter_chapters(category_names))
    assert result == expected_output

def test_filter_chapters_threshold_exactly_met():
    category_names = {
        "Category1": {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}},
        "Category2": {"Chapter1": {}, "Chapter2": {}, "Chapter3": {}}
    }
    expected_output = []

    result = list(filter_chapters(category_names))
    assert result == expected_output

def test_filter_chapters_generator_behavior():
    category_names = {
        "category1": {"chapter1": {}, "chapter2": {}, "chapter3": {}, "chapter4": {}},
        "category2": {"chapter1": {}, "chapter2": {}},
        "category3": {"chapter1": {}, "chapter2": {}, "chapter3": {}, "chapter4": {}, "chapter5": {}}
    }

    generator = filter_chapters(category_names)

    assert next(generator) == ("category1", {"chapter1": {}, "chapter2": {}, "chapter3": {}, "chapter4": {}})
    assert next(generator) == ("category3", {"chapter1": {}, "chapter2": {}, "chapter3": {}, "chapter4": {}, "chapter5": {}})

    with pytest.raises(StopIteration):
        next(generator)

def test_filter_chapters_large_input():
    large_category_names = {
        f"category{i}": {f"chapter{j}": {} for j in range(i + 1)} for i in range(1000)
    }

    result = list(filter_chapters(large_category_names))

    assert len(result) == 997
    assert all(len(chapters) > 3 for _, chapters in result)
    assert result[0][0] == "category3"
    assert result[-1][0] == "category999"
    assert len(result[-1][1]) == 1000


def test_split_value_single_value():
    result = split_value("high")
    assert result == ["high"]

def test_split_value_multiple_values_comma():
    result = split_value("swordsmanship,archery")
    assert result == ["swordsmanship", "archery"]

def test_split_value_multiple_values_semicolon():
    result = split_value("swordsmanship; archery")
    assert result == ["swordsmanship", "archery"]

def test_split_value_mixed_delimiters():
    result = split_value("swordsmanship, archery; stealth")
    assert result == ["swordsmanship", "archery", "stealth"]

def test_split_value_empty_string():
    result = split_value("")
    assert result == [""]

def test_split_value_whitespace_value():
    result = split_value(" ")
    assert result == [" "]

# Unit tests for add_to_traits

def test_add_to_traits_happy_path_single_value(mock_split_value):
    traits = {}
    result = add_to_traits("strength", "high", traits)
    assert result == {"strength": ["high"]}
    mock_split_value.assert_called_once_with("high")


def test_add_to_traits_happy_path_list_value(mock_split_value):
    traits = {}
    result = add_to_traits("skills", ["swordsmanship", "archery"], traits)
    assert result == {"skills": ["swordsmanship", "archery"]}
    mock_split_value.assert_not_called()


def test_add_to_traits_existing_attribute_single_value(mock_split_value):
    traits = {"strength": ["medium"]}
    result = add_to_traits("strength", "high", traits)
    assert result == {"strength": ["medium", "high"]}
    mock_split_value.assert_called_once_with("high")


def test_add_to_traits_existing_attribute_list_value(mock_split_value):
    traits = {"skills": ["swordsmanship"]}
    result = add_to_traits("skills", ["archery", "stealth"], traits)
    assert result == {"skills": ["swordsmanship", "archery", "stealth"]}
    mock_split_value.assert_not_called()


def test_add_to_traits_edge_case_empty_list(mock_split_value):
    traits = {}
    result = add_to_traits("strength", [], traits)
    assert result == {"strength": []}
    mock_split_value.assert_not_called()


def test_add_to_traits_edge_case_empty_string(mock_split_value):
    traits = {}
    result = add_to_traits("strength", "", traits)
    assert result == {"strength": [""]}
    mock_split_value.assert_called_once_with("")


def test_add_to_traits_new_attribute(mock_split_value):
    traits = {}
    result = add_to_traits("intelligence", "high", traits)
    assert result == {"intelligence": ["high"]}
    mock_split_value.assert_called_once_with("high")


def test_add_to_traits_type_check_string(mock_split_value):
    traits = {"strength": []}
    result = add_to_traits("strength", "high", traits)
    assert result == {"strength": ["high"]}
    mock_split_value.assert_called_once_with("high")


def test_add_to_traits_type_check_list(mock_split_value):
    traits = {"skills": []}
    result = add_to_traits("skills", ["archery"], traits)
    assert result == {"skills": ["archery"]}
    mock_split_value.assert_not_called()


def test_process_chapter_details_happy_path(mock_add_to_traits):
    chapter_details = {
        "setting": "medieval castle",
        "characters": ["knight", "princess"],
        "mood": "mysterious"
    }
    traits = {}

    result = process_chapter_details(chapter_details, traits)

    assert result == {
        "setting": ["medieval castle"],
        "characters": ["knight", "princess"],
        "mood": ["mysterious"]
    }
    assert mock_add_to_traits.call_count == 3

def test_process_chapter_details_empty_input(mock_add_to_traits):
    chapter_details = {}
    traits = {}

    result = process_chapter_details(chapter_details, traits)

    assert result == {}
    assert mock_add_to_traits.call_count == 0

def test_process_chapter_details_existing_traits(mock_add_to_traits):
    chapter_details = {
        "setting": "futuristic city",
        "mood": "tense"
    }
    traits = {
        "characters": ["detective", "android"],
        "mood": ["mysterious"]
    }

    result = process_chapter_details(chapter_details, traits)

    assert result == {
        "characters": ["detective", "android"],
        "setting": ["futuristic city"],
        "mood": ["mysterious", "tense"]
    }
    assert mock_add_to_traits.call_count == 2

def test_process_chapter_details_mixed_value_types(mock_add_to_traits):
    chapter_details = {
        "setting": "space station",
        "characters": ["astronaut", "alien"],
        "themes": "isolation, discovery"
    }
    traits = {}

    result = process_chapter_details(chapter_details, traits)

    assert result == {
        "setting": ["space station"],
        "characters": ["astronaut", "alien"],
        "themes": ["isolation, discovery"]
    }
    assert mock_add_to_traits.call_count == 3

def test_process_chapter_details_all_list_values(mock_add_to_traits):
    chapter_details = {
        "settings": ["moon base", "lunar surface"],
        "characters": ["commander", "scientist"],
        "themes": ["exploration", "survival"]
    }
    traits = {}

    result = process_chapter_details(chapter_details, traits)

    assert result == {
        "settings": ["moon base", "lunar surface"],
        "characters": ["commander", "scientist"],
        "themes": ["exploration", "survival"]
    }
    assert mock_add_to_traits.call_count == 3


def test_iterate_categories_happy_path(mock_process_chapter_details):
    detail_dict = {
        "chapter1": {"setting": "forest", "mood": "mysterious"},
        "chapter2": {"setting": "castle", "characters": ["knight", "dragon"]}
    }

    result = iterate_categories(detail_dict)

    assert result == {
        "setting": ["forest", "castle"],
        "mood": ["mysterious"],
        "characters": ["knight", "dragon"]
    }
    assert mock_process_chapter_details.call_count == 2

def test_iterate_categories_empty_input(mock_process_chapter_details):
    detail_dict = {}

    result = iterate_categories(detail_dict)

    assert result == {}
    assert mock_process_chapter_details.call_count == 0

def test_iterate_categories_single_chapter(mock_process_chapter_details):
    detail_dict = {
        "chapter1": {"setting": "spaceship", "mood": "tense", "characters": ["captain", "alien"]}
    }

    result = iterate_categories(detail_dict)

    assert result == {
        "setting": ["spaceship"],
        "mood": ["tense"],
        "characters": ["captain", "alien"]
    }
    assert mock_process_chapter_details.call_count == 1

def test_iterate_categories_overlapping_attributes(mock_process_chapter_details):
    detail_dict = {
        "chapter1": {"setting": "beach", "mood": "relaxed"},
        "chapter2": {"setting": "ocean", "mood": "tense"},
        "chapter3": {"setting": "island", "mood": "mysterious"}
    }

    result = iterate_categories(detail_dict)

    assert result == {
        "setting": ["beach", "ocean", "island"],
        "mood": ["relaxed", "tense", "mysterious"]
    }
    assert mock_process_chapter_details.call_count == 3

def test_iterate_categories_mixed_value_types(mock_process_chapter_details):
    detail_dict = {
        "chapter1": {"setting": "city", "characters": ["detective"]},
        "chapter2": {"setting": "alley", "characters": "criminal"},
        "chapter3": {"setting": "police station", "characters": ["officer", "witness"]}
    }

    result = iterate_categories(detail_dict)

    assert result == {
        "setting": ["city", "alley", "police station"],
        "characters": ["detective", "criminal", "officer", "witness"]
    }
    assert mock_process_chapter_details.call_count == 3

def test_create_description_with_list():
    details = ["apple", "banana", "cherry"]
    result = create_description(details)
    assert result == "apple, banana, cherry"

def test_create_description_with_single_item_list():
    details = ["solo"]
    result = create_description(details)
    assert result == "solo"

def test_create_description_with_empty_list():
    details = []
    result = create_description(details)
    assert result == ""

def test_create_description_with_dict(mock_iterate_categories):
    details = {"chapter1": {"setting": "forest", "mood": "mysterious"}}
    mock_iterate_categories.return_value = {
        "setting": ["forest"],
        "mood": ["mysterious"]
    }

    result = create_description(details)

    assert result == "setting: forest; mood: mysterious"
    mock_iterate_categories.assert_called_once_with(details)

def test_create_description_with_complex_dict(mock_iterate_categories):
    details = {
        "chapter1": {"setting": "castle", "characters": ["knight", "dragon"]},
        "chapter2": {"setting": "forest", "mood": "mysterious"}
    }
    mock_iterate_categories.return_value = {
        "setting": ["castle", "forest"],
        "characters": ["knight", "dragon"],
        "mood": ["mysterious"]
    }

    result = create_description(details)

    assert result == "setting: castle, forest; characters: knight, dragon; mood: mysterious"
    mock_iterate_categories.assert_called_once_with(details)

def test_create_description_with_empty_dict(mock_iterate_categories):
    details = {}
    mock_iterate_categories.return_value = {}

    result = create_description(details)

    assert result == ""
    mock_iterate_categories.assert_called_once_with(details)

def test_create_description_with_single_item_dict(mock_iterate_categories):
    details = {"chapter1": {"setting": "beach"}}
    mock_iterate_categories.return_value = {"setting": ["beach"]}

    result = create_description(details)

    assert result == "setting: beach"
    mock_iterate_categories.assert_called_once_with(details)

def test_create_description_with_multiple_values(mock_iterate_categories):
    details = {"chapter1": {"characters": ["hero", "villain", "sidekick"]}}
    mock_iterate_categories.return_value = {"characters": ["hero", "villain", "sidekick"]}

    result = create_description(details)

    assert result == "characters: hero, villain, sidekick"
    mock_iterate_categories.assert_called_once_with(details)

def test_generate_prompts_happy_path(mock_filter_chapters, mock_create_description):
    mock_filter_chapters.return_value = [
        ("Chapter 1", {"setting": "forest"}),
        ("Chapter 2", {"setting": "castle"})
    ]
    mock_create_description.side_effect = ["forest description", "castle description"]

    category = "test_category"
    category_names = {"test_category": {"Chapter 1": {}, "Chapter 2": {}}}

    result = list(generate_prompts(category, category_names))

    assert result == [
        ("test_category", "Chapter 1", "Chapter 1: forest description"),
        ("test_category", "Chapter 2", "Chapter 2: castle description")
    ]
    mock_filter_chapters.assert_called_once_with(category_names)
    assert mock_create_description.call_count == 2

def test_generate_prompts_empty_input(mock_filter_chapters, mock_create_description):
    mock_filter_chapters.return_value = []

    category = "empty_category"
    category_names = {}

    result = list(generate_prompts(category, category_names))

    assert not result
    mock_filter_chapters.assert_called_once_with(category_names)
    mock_create_description.assert_not_called()

def test_generate_prompts_single_chapter(mock_filter_chapters, mock_create_description):
    mock_filter_chapters.return_value = [("Solo Chapter", {"mood": "mysterious"})]
    mock_create_description.return_value = "mysterious mood"

    category = "single_chapter_category"
    category_names = {"single_chapter_category": {"Solo Chapter": {}}}

    result = list(generate_prompts(category, category_names))

    assert result == [("single_chapter_category", "Solo Chapter", "Solo Chapter: mysterious mood")]
    mock_filter_chapters.assert_called_once_with(category_names)
    mock_create_description.assert_called_once()

def test_generate_prompts_generator_behavior(mock_filter_chapters, mock_create_description):
    mock_filter_chapters.return_value = [
        ("Chapter A", {"character": "hero"}),
        ("Chapter B", {"character": "villain"}),
        ("Chapter C", {"character": "sidekick"})
    ]
    mock_create_description.side_effect = ["hero description", "villain description", "sidekick description"]

    category = "generator_test_category"
    category_names = {"generator_test_category": {"Chapter A": {}, "Chapter B": {}, "Chapter C": {}}}

    generator = generate_prompts(category, category_names)

    assert next(generator) == ("generator_test_category", "Chapter A", "Chapter A: hero description")
    assert next(generator) == ("generator_test_category", "Chapter B", "Chapter B: villain description")
    assert next(generator) == ("generator_test_category", "Chapter C", "Chapter C: sidekick description")

    with pytest.raises(StopIteration):
        next(generator)

def test_generate_prompts_large_input(mock_filter_chapters, mock_create_description):
    mock_filter_chapters.return_value = [
        (f"Chapter {i}", {"content": f"content {i}"}) for i in range(1000)
    ]
    mock_create_description.side_effect = [f"description {i}" for i in range(1000)]

    category = "large_category"
    category_names = {"large_category": {f"Chapter {i}": {} for i in range(1000)}}

    generator = generate_prompts(category, category_names)

    for i in range(1000):
        assert next(generator) == (
            "large_category",
            f"Chapter {i}",
            f"Chapter {i}: description {i}"
        )

    with pytest.raises(StopIteration):
        next(generator)

    assert mock_filter_chapters.call_count == 1
    assert mock_create_description.call_count == 1000


def test_create_prompts_single_category(mock_generate_prompts):
    mock_generate_prompts.return_value = iter([
        ("category1", "name1", "name1: description1"),
        ("category1", "name2", "name2: description2")
    ])

    lorebinder = {
        "category1": {"name1": {}, "name2": {}}
    }

    result = list(create_prompts(lorebinder))

    assert result == [
        ("category1", "name1", "name1: description1"),
        ("category1", "name2", "name2: description2")
    ]
    mock_generate_prompts.assert_called_once_with("category1", {"name1": {}, "name2": {}})

def test_create_prompts_multiple_categories(mock_generate_prompts):
    mock_generate_prompts.side_effect = [
        iter([("category1", "name1", "name1: description1")]),
        iter([("category2", "name2", "name2: description2")])
    ]

    lorebinder = {
        "category1": {"name1": {}},
        "category2": {"name2": {}}
    }

    result = list(create_prompts(lorebinder))

    assert result == [
        ("category1", "name1", "name1: description1"),
        ("category2", "name2", "name2: description2")
    ]
    assert mock_generate_prompts.call_count == 2
    mock_generate_prompts.assert_any_call("category1", {"name1": {}})
    mock_generate_prompts.assert_any_call("category2", {"name2": {}})

def test_create_prompts_empty_lorebinder(mock_generate_prompts):
    lorebinder = {}

    result = list(create_prompts(lorebinder))

    assert not result
    mock_generate_prompts.assert_not_called()

def test_create_prompts_empty_category(mock_generate_prompts):
    mock_generate_prompts.return_value = iter([])

    lorebinder = {
        "empty_category": {}
    }

    result = list(create_prompts(lorebinder))

    assert not result
    mock_generate_prompts.assert_called_once_with("empty_category", {})

def test_create_prompts_generator_behavior(mock_generate_prompts):
    mock_generate_prompts.side_effect = [
        iter([("category1", "name1", "name1: description1")]),
        iter([("category2", "name2", "name2: description2")])
    ]

    lorebinder = {
        "category1": {"name1": {}},
        "category2": {"name2": {}}
    }

    generator = create_prompts(lorebinder)

    assert next(generator) == ("category1", "name1", "name1: description1")
    assert next(generator) == ("category2", "name2", "name2: description2")

    with pytest.raises(StopIteration):
        next(generator)

def test_create_prompts_large_input(mock_generate_prompts):
    large_category = {f"name{i}": {} for i in range(1000)}
    mock_generate_prompts.return_value = iter([
        ("large_category", f"name{i}", f"name{i}: description{i}")
        for i in range(1000)
    ])

    lorebinder = {
        "large_category": large_category
    }

    generator = create_prompts(lorebinder)

    for i in range(1000):
        assert next(generator) == ("large_category", f"name{i}", f"name{i}: description{i}")

    with pytest.raises(StopIteration):
        next(generator)

    mock_generate_prompts.assert_called_once_with("large_category", large_category)
