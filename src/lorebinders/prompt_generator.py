import re
from collections.abc import Generator


def filter_chapters(
    category_names: dict[str, dict],
) -> Generator[tuple[str, dict[str, dict]], None, None]:
    """Filter chapters that meet minimum threshold.

    Args:
        category_names: Dictionary mapping category names to chapter data.

    Yields:
        Tuple of name and chapters data for categories meeting threshold.
    """
    minimum_chapter_threshold = 3
    for name, chapters in category_names.items():
        if len(chapters) > minimum_chapter_threshold:
            yield name, chapters


def split_value(value: str) -> list[str]:
    """Split value by comma or semicolon.

    Args:
        value: String to split.

    Returns:
        List of split values.
    """
    return re.split(r"[;,]\s*", value)


def add_to_traits(
    attribute: str,
    value: str | list[str],
    traits: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Add value to traits dictionary.

    Args:
        attribute: The trait attribute name.
        value: Value or list of values to add.
        traits: Dictionary to add traits to.

    Returns:
        Updated traits dictionary.
    """
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
    """Process chapter details and add to traits.

    Args:
        chapter_details: Details from a chapter.
        traits: Existing traits dictionary.

    Returns:
        Updated traits dictionary.
    """
    for attribute, value in chapter_details.items():
        traits = add_to_traits(attribute, value, traits)
    return traits


def iterate_categories(
    detail_dict: dict[str, dict[str, str | list[str]]],
) -> dict[str, list[str]]:
    """Iterate through categories and build traits.

    Args:
        detail_dict: Dictionary of detailed information by category.

    Returns:
        Aggregated traits dictionary.
    """
    traits: dict[str, list[str]] = {}
    for chapter_details in detail_dict.values():
        traits = process_chapter_details(chapter_details, traits)
    return traits


def create_description(details: dict | list) -> str:
    """Create description from details.

    Args:
        details: Either a list of details or dict of categorized details.

    Returns:
        Formatted description string.
    """
    if not isinstance(details, dict):
        return ", ".join(details)
    traits = iterate_categories(details)
    return "; ".join(
        f"{trait}: {', '.join(detail)}" for trait, detail in traits.items()
    )


def generate_prompts(
    category: str, category_names: dict[str, dict]
) -> Generator[tuple[str, str, str], None, None]:
    """Generate prompts for summarization.

    Args:
        category: The category name.
        category_names: Dictionary mapping names to chapter data.

    Yields:
        Tuple of category, name, and description.
    """
    for name, chapters in filter_chapters(category_names):
        description = create_description(chapters)
        yield category, name, f"{name}: {description}"


def create_prompts(
    lorebinder: dict[str, dict[str, dict]],
) -> Generator[tuple[str, str, str], None, None]:
    """Create prompts from lorebinder data.

    Args:
        lorebinder: Dictionary containing categorized story data.

    Yields:
        Tuple of category, name, and prompt text.
    """
    for category, category_names in lorebinder.items():
        yield from generate_prompts(category, category_names)
