from typing import Generator


def filter_chapters(
    category_names: dict[str, dict],
) -> Generator[tuple[str, dict[str, dict]], None, None]:
    MINIMUM_CHAPTER_THRESHOLD = 3
    for name, chapters in category_names.items():
        if len(chapters) > MINIMUM_CHAPTER_THRESHOLD:
            yield name, chapters


def add_to_traits(
    attribute: str,
    value: str | list[str],
    traits: dict[str, list[str]],
) -> None:
    if attribute not in traits:
        traits[attribute] = []
    if isinstance(value, list):
        traits[attribute].extend(value)
    else:
        process_value(attribute, value, traits)


def process_value(
    attribute: str, value: str, traits: dict[str, list[str]]
) -> None:
    if ";" in value or "," in value:
        value = value.replace("; ", ",")
        traits[attribute].extend(value.split(","))
    else:
        traits[attribute].append(value)


def process_chapter_details(
    chapter_details: dict[str, str | list[str]],
    traits: dict[str, list[str]],
) -> None:
    for attribute, value in chapter_details.items():
        add_to_traits(attribute, value, traits)


def iterate_categories(
    detail_dict: dict[str, dict[str, str | list[str]]],
) -> dict[str, list[str]]:
    traits: dict[str, list[str]] = {}
    for chapter_details in detail_dict.values():
        process_chapter_details(chapter_details, traits)
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
