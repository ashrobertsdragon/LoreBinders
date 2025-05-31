import re
from collections import ChainMap
from collections.abc import Callable
from itertools import combinations

from lorebinders._titles import TITLES


def remove_titles(name: str) -> str:
    """Remove titles from a given name.

    Checks if the first word is a title from a predefined list and
    removes it if found.

    Args:
        name: The name from which titles need to be removed.

    Returns:
        The name without any titles.

    Raises:
        TypeError: If name is not a string.
    """
    if not isinstance(name, str):
        raise TypeError("name must be a string")

    name_split: list[str] = name.split(" ")
    if name_split[0].lower() in TITLES and name.lower() not in TITLES:
        return " ".join(name_split[1:])
    return name


def to_singular(plural: str) -> str:
    """Convert a plural word to its singular form.

    Uses common English pluralization rules to convert plural words to
    their singular forms.

    Args:
        plural: A string representing the plural form of a word.

    Returns:
        The singular form of the word if a pattern matches, otherwise
        the original word.

    Raises:
        TypeError: If plural is not a string.
        ValueError: If plural is empty.
    """
    if not isinstance(plural, str):
        raise TypeError("plural must be a string")
    if not plural:
        raise ValueError("plural must not be empty")
    lower_plural = plural.lower()
    patterns = [
        (r"(\w+)(ves)$", r"\1f"),
        (r"(\w+)(ies)$", r"\1y"),
        (r"(\w+)(i)$", r"\1us"),
        (r"(\w+)(a)$", r"\1um"),
        (r"(\w+)(en)$", r"\1an"),
        (r"(\w+)(oes)$", r"\1o"),
        (r"(\w+)(sses)$", r"\1s"),
        (r"(\w+)(ses)$", r"\1se"),
        (r"(\w+)(hes)$", r"\1h"),
        (r"(\w+)(xes)$", r"\1x"),
        (r"(\w+)(zes)$", r"\1ze"),
    ]

    singular = (
        re.sub(pattern, repl, lower_plural)
        for pattern, repl in patterns
        if re.match(pattern, lower_plural)
    )

    return next(singular, lower_plural[:-1])


def clean_list(unparsed_list: list) -> list:
    """Remove "none found" from values in a list.

    Args:
        unparsed_list: The list to be cleaned.

    Returns:
        The cleaned list.
    """
    new_list: list = []
    for item in unparsed_list:
        if isinstance(item, str):
            if cleaned_str := clean_str(item):
                new_list.append(cleaned_str)
        elif isinstance(item, dict):
            if cleaned_dict := clean_none_found(item):
                new_list.append(cleaned_dict)
        elif cleaned_list := clean_list(item):
            new_list.append(cleaned_list)

    return new_list


def clean_str(unparsed_str: str) -> str:
    """Remove "none found" from a string.

    Args:
        unparsed_str: The string to be cleaned.

    Returns:
        The cleaned string.
    """
    return unparsed_str if unparsed_str.lower() != "none found" else ""


def clean_none_found(unparsed_dict: dict) -> dict:
    """Remove "none found" from values in a dictionary.

    Args:
        unparsed_dict: The dictionary to be cleaned.

    Returns:
        The cleaned dictionary.
    """
    new_dict: dict = {}
    for key, value in unparsed_dict.items():
        if isinstance(value, dict):
            if cleaned_dict := clean_none_found(value):
                new_dict[key] = cleaned_dict
        elif isinstance(value, list):
            cleaned_list = clean_list(value)
            cleaned_list_length = len(cleaned_list)
            if cleaned_list_length == 1:
                new_dict[key] = cleaned_list[0]
            elif cleaned_list_length > 1:
                new_dict[key] = cleaned_list
        elif cleaned_str := clean_str(value):
            new_dict[key] = cleaned_str
    return new_dict


class DeduplicateKeys:
    """Remove duplicate keys by merging singular and plural forms.

    This class identifies and merges similar keys in dictionaries,
    particularly focusing on singular/plural variations and title
    matching.
    """

    def deduplicate(self, binder: dict) -> dict:
        """Remove duplicate keys by merging singular and plural forms.

        Args:
            binder: The dictionary to deduplicate.

        Returns:
            The deduplicated dictionary.
        """
        cleaned_dict: dict = {}

        for outer_key, nested_dict in binder.items():
            if not isinstance(nested_dict, dict):
                cleaned_dict[outer_key] = nested_dict
                continue
            duplicate_keys = set()
            for key1, key2 in combinations(nested_dict.keys(), 2):
                if key1 in duplicate_keys or key2 in duplicate_keys:
                    continue
                if self._is_similar_key(key1, key2):
                    key_to_merge, key_to_keep = self._prioritize_keys(
                        key1, key2
                    )
                    nested_dict[key_to_keep] = self._merge_values(
                        nested_dict[key_to_keep], nested_dict[key_to_merge]
                    )
                    duplicate_keys.add(key_to_merge)

            inner_dict: dict = {
                key: value
                for key, value in nested_dict.items()
                if key not in duplicate_keys
            }
            cleaned_dict[outer_key] = inner_dict
        return self._deduplicate_across_dictionaries(cleaned_dict)

    def _prioritize_keys(self, key1: str, key2: str) -> tuple[str, str]:
        """Determine priority of keys based on title status or length.

        Args:
            key1: First key to compare.
            key2: Second key to compare.

        Returns:
            Tuple of (lower_priority, higher_priority) keys.
        """
        lower_key1: str = key1.lower()
        lower_key2: str = key2.lower()

        if (
            lower_key1 in lower_key2 or lower_key2 in lower_key1
        ) and lower_key1 != lower_key2:
            key1_is_title: bool = self._is_title(key1)
            if key1_is_title:
                return key2, key1
            key2_is_title: bool = self._is_title(key2)
            if key2_is_title:
                return key1, key2
        lower_p, higher_p = sorted([key1, key2], key=len)
        return lower_p, higher_p

    def _is_similar_key(self, key_1: str, key_2: str) -> bool:
        """Determine if two keys are similar.

        Checks for similarity based on singular/plural forms, title
        matching, and word containment after removing titles.

        Args:
            key_1: The first key to compare.
            key_2: The second key to compare.

        Returns:
            True if the keys are similar, False otherwise.
        """
        key1 = key_1.strip().lower()
        key2 = key_2.strip().lower()
        detitled_key1 = remove_titles(key1)
        detitled_key2 = remove_titles(key2)
        singular_key1 = to_singular(key1)
        singular_key2 = to_singular(key2)

        if any([
            key1 == key2,
            key1 == singular_key2,
            singular_key1 == key2,
            singular_key1 == singular_key2,
        ]):
            return True

        key1_is_title = self._is_title(key1)
        key2_is_title = self._is_title(key2)
        if (key1_is_title and key1 + " " in key2) or (
            key2_is_title and key2 + " " in key1
        ):
            return True

        if detitled_key1 != key1 or detitled_key2 != key2:
            return any([
                detitled_key1 == key2,
                key1 == detitled_key2,
                detitled_key1 == detitled_key2,
                detitled_key1 == singular_key2,
                singular_key1 == detitled_key2,
                detitled_key1 + " " in key2,
                detitled_key2 + " " in key1,
                key1 + " " in detitled_key2,
                key2 + " " in detitled_key1,
            ])
        return False

    def _is_title(self, key: str) -> bool:
        """Check if key is a title in TITLES list.

        Args:
            key: The key to check.

        Returns:
            True if key is a title, False otherwise.
        """
        return key.lower() in TITLES

    def _deduplicate_across_dictionaries(self, summaries: dict) -> dict:
        """Find duplicates across dictionaries and merge their values.

        Specifically looks for duplicate keys in character dictionaries
        and merges their values.

        Args:
            summaries: The dictionary containing the summaries.

        Returns:
            The updated summaries dictionary with duplicates merged.
        """
        characters_dict: dict = summaries.setdefault("Characters", {})

        deduplicated_summaries: dict = {}
        for category, names in list(summaries.items()):
            if category == "Characters":
                deduplicated_summaries[category] = names
                continue
            for name in names:
                if characters_dict.get(name) is None:
                    deduplicated_summaries[category] = {name: names[name]}
                    continue
                for chapter, details in names[name].items():
                    if chapter in characters_dict[name]:
                        merged_values = self._merge_values(
                            characters_dict[name][chapter], details
                        )
                        deduplicated_summaries["Characters"][name][chapter] = (
                            merged_values
                        )
                    elif isinstance(details, dict):
                        deduplicated_summaries["Characters"][name][chapter] = (
                            details
                        )
                    else:
                        deduplicated_summaries["Characters"][name][chapter] = {
                            "Also": details
                        }

        return deduplicated_summaries

    def _merge_values(
        self,
        value1: dict | list | str,
        value2: dict | list | str,
    ) -> dict | list | str:
        """Merge two dictionary key values of unknown datatypes.

        Args:
            value1: A dictionary key value.
            value2: A dictionary key value.

        Returns:
            Merged dictionary key value.

        Raises:
            TypeError: If values are not dict, list, or str.
        """
        if not isinstance(value1, (dict, list, str)):
            raise TypeError(
                "Value1 must be either a dictionary, list, or string"
            )
        if not isinstance(value2, (dict, list, str)):
            raise TypeError(
                "Value2 must be either a dictionary, list, or string"
            )

        also_key = "Also"
        if isinstance(value1, dict) and isinstance(value2, dict):
            return dict(ChainMap(value1, value2))
        elif isinstance(value1, list) and isinstance(value2, list):
            return value1 + value2
        elif isinstance(value1, list) and isinstance(value2, dict):
            merged_list: list = []
            for item in value1:
                if isinstance(item, dict):
                    merged_item = dict(ChainMap(item, value2))
                    merged_list.append(merged_item)
                else:
                    merged_list.append(item)
            for key, value in value2.items():
                if all(key not in d for d in merged_list):
                    merged_list.append({key: value})
            return merged_list
        elif isinstance(value1, dict) and isinstance(value2, list):
            merged_dict: dict = value1.copy()
            if value1.get(also_key) is not None:
                merged_dict[also_key] = self._merge_values(
                    merged_dict[also_key], value2
                )
                return merged_dict
            else:
                value1[also_key] = value2
        elif isinstance(value1, dict):
            for key in value1:
                if key == value2:
                    return value1
            value1[also_key] = value2
        elif isinstance(value2, list):
            value2.append(value1)
            return value2
        else:
            return [value1, value2]
        return value1


def reshape_dict(binder: dict) -> dict:
    """Reshape dictionary to demote chapter numbers inside category names.

    Args:
        binder: The dictionary to be reshaped.

    Returns:
        The reshaped dictionary.
    """
    reshaped_data: dict = {}
    for chapter, chapter_data in binder.items():
        for category, category_data in chapter_data.items():
            category_key = category.title()
            reshaped_data.setdefault(category_key, {})
            for name, name_details in category_data.items():
                reshaped_data[category_key].setdefault(name, {})
                reshaped_data[category_key][name][chapter] = name_details

    return reshaped_data


def final_reshape(binder: dict) -> dict:
    """Demote chapter numbers to lowest level in Characters/Settings.

    Args:
        binder: The dictionary to be reshaped.

    Returns:
        The reshaped dictionary.
    """
    reshaped_data: dict = {}
    for category, names in binder.items():
        if category not in ["Characters", "Settings"]:
            reshaped_data[category] = names
            continue

        reshaped_data.setdefault(category, {})
        for name, chapters in names.items():
            name_data = reshaped_data[category].setdefault(name, {})
            for chapter, traits in chapters.items():
                if not isinstance(traits, dict):
                    name_data[chapter] = traits
                for trait, detail in traits.items():
                    name_data.setdefault(trait, {})[chapter] = detail
    return reshaped_data


def sort_dictionary(binder: dict) -> dict:
    """Sort the keys of a nested dictionary.

    Args:
        binder: The dictionary to be sorted.

    Returns:
        Dictionary with the same structure but keys sorted in ascending
        order.

    Raises:
        TypeError: If inner dictionary doesn't have integer keys.
    """
    sorted_dict = {}
    for outer_key, nested_dict in binder.items():
        sorted_middle_dict = {}
        for key, inner_dict in sorted(nested_dict.items()):
            if isinstance(inner_dict, dict) and all(
                isinstance(k, int) for k in inner_dict
            ):
                sorted_inner_dict = {
                    str(k): inner_dict[k] for k in sorted(inner_dict)
                }
                sorted_middle_dict[key] = sorted_inner_dict
            else:
                raise TypeError(
                    f"Expected a dictionary with integer keys for '{key}', "
                    f"but got: {type(inner_dict).__name__} with keys "
                    f"{list(inner_dict.keys())}"
                )
            sorted_dict[outer_key] = sorted_middle_dict

    return sorted_dict


class ReplaceNarrator:
    """Replace narrator references with a specified character name.

    Replaces occurrences of 'narrator', 'protagonist', 'main character'
    and similar terms with a specified narrator name throughout a
    dictionary structure.
    """

    def __init__(self, binder: dict):
        """Initialize the ReplaceNarrator instance.

        Args:
            binder: The dictionary to process.
        """
        self._binder = binder

    def _replace_str(self, value: str) -> str:
        """Replace narrator references in a string.

        Args:
            value: The string to process.

        Returns:
            String with narrator references replaced.
        """
        narrator_list: str = (
            r"\b(narrator|the narrator|the protagonist|"
            r"protagonist|the main character|main character)\b"
        )
        return re.sub(narrator_list, self._narrator_name, value.lower())

    def _clean_dict(self, value: dict) -> dict:
        """Recursively replace narrator references in a dictionary.

        Args:
            value: The dictionary to process.

        Returns:
            Dictionary with narrator references replaced.
        """
        new_dict: dict = {}
        for key, val in value.items():
            cleaned_key = self._replace_str(key)
            new_dict[cleaned_key] = self._handle_value(val)
        return new_dict

    def _clean_list(self, value: list) -> list:
        """Replace narrator references in a list.

        Args:
            value: The list to process.

        Returns:
            List with narrator references replaced.
        """
        return [self._replace_str(val) for val in value]

    def _handle_value(self, value: dict | list | str) -> dict | list | str:
        """Handle value replacement based on type.

        Args:
            value: The value to process (dict, list, or str).

        Returns:
            Processed value with narrator references replaced.
        """
        type_handlers: dict[type, Callable] = {
            dict: self._clean_dict,
            list: self._clean_list,
            str: self._replace_str,
        }
        value_type = type(value)
        if value_type in type_handlers:
            return type_handlers[value_type](value)
        else:
            return value

    def replace(self, narrator_name: str) -> dict:
        """Replace narrator, protagonist and synonyms with character name.

        Args:
            narrator_name: The name to replace narrator references with.

        Returns:
            Dictionary with narrator references replaced.
        """
        self._narrator_name = narrator_name
        return self._clean_dict(self._binder)


def clean_lorebinders(lorebinder: dict, narrator: str) -> dict:
    """Clean and process lorebinder dictionary.

    Args:
        lorebinder: The lorebinder dictionary to process.
        narrator: The narrator name for replacement.

    Returns:
        Cleaned and processed lorebinder dictionary.
    """
    reshaped: dict = reshape_dict(lorebinder)

    only_found: dict = clean_none_found(reshaped)

    deduplicator = DeduplicateKeys()
    deduped: dict = deduplicator.deduplicate(only_found)

    replace_narrator = ReplaceNarrator(deduped)
    narrator_replaced: dict = replace_narrator.replace(narrator)
    return sort_dictionary(narrator_replaced)
