import re
from typing import Generator


def filter_chapters(
    category_names: dict[str, dict],
) -> Generator[tuple[str, dict[str, dict]], None, None]:
    MINIMUM_CHAPTER_THRESHOLD = 3
    for name, chapters in category_names.items():
        if len(chapters) > MINIMUM_CHAPTER_THRESHOLD:
            yield name, chapters


def split_value(value: str) -> list[str]:
    return re.split(r"[;,]\s*", value)


def add_to_traits(
    attribute: str,
    value: str | list[str],
    traits: dict[str, list[str]],
) -> dict[str, list[str]]:
    if attribute not in traits:
        traits[attribute] = []
    if isinstance(value, list):
        traits[attribute].extend(value)
    else:
        traits[attribute].extend(split_value(value))
    return traits


def process_chapter_details(
    chapter_details: dict[str, str | list[str]],
    traits: dict[str, list[str]],
) -> dict[str, list[str]]:
    for attribute, value in chapter_details.items():
        traits = add_to_traits(attribute, value, traits)
    return traits


def iterate_categories(
    detail_dict: dict[str, dict[str, str | list[str]]],
) -> dict[str, list[str]]:
    traits: dict[str, list[str]] = {}
    for chapter_details in detail_dict.values():
        traits = process_chapter_details(chapter_details, traits)
    return traits


def create_description(details: dict | list) -> str:
    if not isinstance(details, dict):
        return ", ".join(details)
    traits = iterate_categories(details)
    return "; ".join(
        f"{trait}: {', '.join(detail)}" for trait, detail in traits.items()
    )


def generate_prompts(
    category: str, category_names: dict[str, dict]
) -> Generator[tuple[str, str, str], None, None]:
    for name, chapters in filter_chapters(category_names):
        description = create_description(chapters)
        yield category, name, f"{name}: {description}"


def create_prompts(
    lorebinder: dict[str, dict[str, dict]],
) -> Generator[tuple[str, str, str], None, None]:
    for category, category_names in lorebinder.items():
        yield from generate_prompts(category, category_names)
