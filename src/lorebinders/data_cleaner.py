import re
from collections import ChainMap, defaultdict
from itertools import combinations
from typing import Callable, Dict, List, Tuple, Union, cast

from ._titles import TITLES


class Data:
    pass


class ManipulateData(Data):
    def remove_titles(self, name: str) -> str:
        """
        Removes titles from a given name.

        This method takes a name as input and removes any titles from the
        beginning of the name. It checks if the first word of the name is a
        title, based on a predefined list of titles. If the first word is a
        title, it returns the name without the title. Otherwise, it returns
        the original name.

        Args:
            value (str): The name from which titles need to be removed.

        Returns:
            str: The name without any titles.

        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")

        name_split: List[str] = name.split(" ")
        if name_split[0] in TITLES and name not in TITLES:
            return " ".join(name_split[1:])
        return name

    def to_singular(self, plural: str) -> str:
        """
        Converts a plural word to its singular form based on common English
        pluralization rules.

        Args:
            plural: A string representing the plural form of a word.

        Returns:
            (str) The singular form of the given word if a pattern matches,
                otherwise the original word.
        """
        if not isinstance(plural, str):
            raise TypeError("plural must be a string")
        if not plural:
            raise ValueError("plural must not be empty")
        lower_plural = plural.lower()
        patterns = {
            r"(\w+)(ves)$": r"\1f",
            r"(\w+)(ies)$": r"\1y",
            r"(\w+)(i)$": r"\1us",
            r"(\w+)(a)$": r"\1um",
            r"(\w+)(en)$": r"\1an",
            r"(\w+)(oes)$": r"\1o",
            r"(\w+)(ses)$": r"\1s",
            r"(\w+)(hes)$": r"\1h",
            r"(\w+)(xes)$": r"\1x",
            r"(\w+)(zes)$": r"\1z",
        }

        singular = (
            re.sub(pattern, repl, lower_plural)
            for pattern, repl in patterns.items()
        )
        return next(singular, plural[:-1])


class CleanData(Data):
    def __init__(self, binder: dict):
        self.binder = binder


class RemoveNoneFound(CleanData):
    """
    This class removes "None found" entries from a nested dictionary.

    Args:
        binder (dict): The nested dictionary to be cleaned.

    Attributes:
        binder (dict): The nested dictionary to be cleaned.

    Methods:
        _remove_none: Recursively removes "None found" entries from the nested
            dictionary.
        clean_none_found: Calls `_remove_none`.
    """

    def clean_none_found(self) -> dict:
        """
        Calls the _remove_none method to recursively remove "None found"
        entries from the binder dictionary the class was initialized with.
        """
        return self._remove_none(self.binder)

    def _remove_none(self, d: Union[dict, list, str]) -> dict:
        """
        Takes the nested dictionary from AttributeAnalyzer and removes "None
        found" entries.
        Returns the cleaned nested dictionary.
        """
        if isinstance(d, dict):
            new_dict: dict = {}
            for key, value in d.items():
                cleaned_value = self._remove_none(value)
                if isinstance(cleaned_value, list):
                    new_dict[key] = (
                        cleaned_value
                        if len(cleaned_value) > 1
                        else cleaned_value[0]
                    )
                elif (
                    isinstance(cleaned_value, str)
                    and cleaned_value.lower() != "none found"
                ):
                    new_dict[key] = cleaned_value
            return new_dict
        # Use cast pretend to convert lists and strings to dicts for MyPy
        elif isinstance(d, list):
            cleaned_list = [
                self._remove_none(item)
                for item in d
                if item.lower() != "none found"
            ]
            if len(cleaned_list) > 1:
                return cast(dict, cleaned_list)
            elif len(cleaned_list) == 1:
                return cast(dict, cleaned_list[0])
            else:
                return {}
        else:
            return {} if d.lower() == "none found" else cast(dict, {d: None})


class DeduplicateKeys(CleanData):
    """
    This class removes duplicate keys in a dictionary by merging singular and
    plural forms of keys. It uses the __call__ method to be called directly.

    Args:
        binder (dict): The dictionary to be sorted

    Attributes:
        manipulate_data (ManipulateData): An instance of the ManipulateData
            class.

    Methods:
        _deduplicate_keys: Removes duplicate keys in a dictionary by merging
            singular and plural forms of keys.
        _prioritize_keys: Determines the priority of keys based on whether one
            is a standalone title or length.
        _is_similar_key: Determines if two keys are similar based on certain
            conditions.
        _is_title: Checks if a key is a title in the TITLES list.
        _deduplicate_across_dictionaries: Finds duplicates across dictionaries
            and merges their values.
        _merge_values: Merges two dictionary key values of unknown datatypes
            into one.
    """

    def __init__(self, binder: dict) -> None:
        self.manipulate_data = ManipulateData()
        super().__init__(binder)

    def __call__(self) -> None:
        self.deduplicated = self._deduplicate_keys(self.binder)

    def _deduplicate_keys(self, d: dict) -> dict:
        """
        Removes duplicate keys in a dictionary by merging singular and plural
        forms of keys.

        Args:
            dictionary: The dictionary to deduplicate.

        Returns the deduplicated dictionary.
        """

        cleaned_dict = {}

        for outer_key, nested_dict in d.items():
            if not isinstance(nested_dict, dict):
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

            inner_dict = {
                key: value
                for key, value in nested_dict.items()
                if key not in duplicate_keys
            }
            cleaned_dict[outer_key] = inner_dict
        return self._deduplicate_across_dictionaries(cleaned_dict)

    def _prioritize_keys(self, key1: str, key2: str) -> Tuple[str, str]:
        """
        Determines priority of keys, based on whether one is standalone title
        or length. Order is lower priority, higher priority.
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
        """
        Determines if two keys are similar.

        This method takes two keys as input and determines if they are similar
        based on certain conditions. It checks if the keys have similar words,
        if one key is a singular or plural form of the other, or if they have
        similar titles. The method also removes titles from the keys and
        converts them to their singular forms before making the comparison.

        Args:
            key_1 (str): The first key to compare.
            key_2 (str): The second key to compare.

        Returns:
            bool: True if the keys are similar, False otherwise.

        """
        key1 = key_1.strip()
        key2 = key_2.strip()
        detitled_key1 = self.manipulate_data.remove_titles(key1)
        detitled_key2 = self.manipulate_data.remove_titles(key2)
        singular_key1 = self.manipulate_data.to_singular(key1)
        singular_key2 = self.manipulate_data.to_singular(key2)

        if (
            key1 + " " in key2
            or key2 + " " in key1
            or key1 == singular_key2
            or singular_key1 == key2
        ):
            return True

        key1_is_title = self._is_title(key1)
        key2_is_title = self._is_title(key2)
        if (key1_is_title and key1.lower() in key2.lower()) or (
            key2_is_title and key2.lower() in key1.lower()
        ):
            return True

        if detitled_key1 and detitled_key2:
            return (
                detitled_key1 == key2
                or key1 == detitled_key2
                or detitled_key1 == singular_key2
                or singular_key1 == detitled_key2
                or detitled_key1 + " " in key2
                or detitled_key2 + " " in key1
                or key1 + " " in detitled_key2
                or key2 + " " in detitled_key1
            )
        return False

    def _is_title(self, key: str) -> bool:
        """Checks if key is a title in TITLES list. Returns Boolean"""
        return key.lower() in TITLES

    def _deduplicate_across_dictionaries(self, summaries: dict) -> dict:
        """
        Finds duplicates across dictionaries.

        This method takes a dictionary 'summaries' as input and finds
        duplicates across dictionaries within it. It specifically looks for
        duplicate keys in the 'names' dictionaries and merges their values.

        Args:
            summaries (dict): The dictionary containing the summaries.

        Returns:
            dict: The updated 'summaries' dictionary with duplicates merged.

        """

        characters_dict: dict = summaries.setdefault("Characters", {})

        keys_to_delete = []
        for category, names in summaries.items():
            if category == "Characters":
                continue
            for name in names:
                if characters_dict.get(name) is None:
                    continue
                for chapter, details in names[name].items():
                    summaries["Characters"].setdefault(name, {}).setdefault(
                        chapter, details
                    )
                    if chapter in characters_dict[name]:
                        merged_values = self._merge_values(
                            characters_dict[name][chapter], details
                        )
                        summaries["Characters"][name][chapter] = merged_values
                    elif isinstance(details, dict):
                        summaries["Characters"][name][chapter] = details
                    else:
                        summaries["Characters"][name][chapter] = {
                            "Also": details
                        }
                keys_to_delete.append(name)

        for name in keys_to_delete:
            del names[name]

        return summaries

    def _merge_values(
        self,
        value1: Union[dict, list, str],
        value2: Union[dict, list, str],
    ) -> Union[dict, list, str]:
        """
        Merges two dictionary key values of unknown datatypes into one
        Args:
            value1: A dictionary key value
            value2: A dictionary key value

        Returns merged dictionary key value
        """
        if not isinstance(value1, (dict, list, str)):
            raise TypeError(
                "Value1 must be either a dictionary, list, or string"
            )
        if not isinstance(value2, (dict, list, str)):
            raise TypeError(
                "Value2 must be either a dictionary, list, or string"
            )

        ALSO_KEY = "Also"
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
            if value1.get(ALSO_KEY) is not None:
                merged_dict[ALSO_KEY] = self._merge_values(
                    merged_dict[ALSO_KEY], value2
                )
            else:
                value1[ALSO_KEY] = value2
        elif isinstance(value1, dict):
            for key in value1:
                if key == value2:
                    return value1
            value1[ALSO_KEY] = value2
        elif isinstance(value2, list):
            value2.append(value1)
            return value2
        else:
            return [value1, value2]
        return value1


class ReshapeDict(CleanData):
    """
    A class to reshape a dictionary of chapter summaries by demoting chapter
    numbers inside attribute names.

    Args:
        binder (dict): The dictionary to be sorted

    Methods:
        __init__(): Sets the _reshaped_data attribute to an empty defaultdict
            and calls the __init__() method of the parent class CleanData to
            set the binder attribute to from the binder parameter.

        __call__(): Calls the _reshape() method to perform the reshaping of
            the data.

        _reshape(): Reshapes the dictionary of chapter summaries by demoting
            chapter numbers inside attribute names. It iterates over the
            chapters, categories, and names in the original data and stores
            the reshaped data in the _reshaped_data attribute.

    Returns:
        dict: The reshaped dictionary of chapter summaries.
    """

    def __init__(self, binder: dict) -> None:
        self._reshaped_data: dict = defaultdict(dict)
        super().__init__(binder)

    def __call__(self) -> None:
        self.reshaped = self._reshape(self.binder)

    def _reshape(self, binder: dict) -> dict:
        """
        Reshapes a dictionary of chapter summaries to demote chapter numbers
        inside attribute names.
        """

        for chapter, chapter_data in binder.items():
            for category, category_data in chapter_data.items():
                capitalized_category = category.title()
                for name, name_details in category_data.items():
                    self._reshaped_data[capitalized_category][name][
                        chapter
                    ] = name_details
        return self._reshaped_data


class FinalReshape(ReshapeDict):
    """
    A class that demotes chapter numbers to lowest dictionary in Characters
    and Settings dictionaries. Intended to be called directly.

    Args:
        binder (dict): The dictionary to be sorted.

    Methods:
        _reshape(self) -> dict:
            Demotes chapter numbers to the lowest dictionary level in the
                'Characters' and 'Settings' dictionaries.

    Returns:
        dict: The reshaped dictionary with demoted chapter numbers.

    """

    def _reshape(self, binder: dict) -> dict:
        """
        Demotes chapter numbers to lowest dictionary in Characters and
        Settings dictionaries.
        """
        for attribute, names in binder.items():
            if attribute not in {"Characters", "Settings"}:
                self._reshaped_data[attribute] = names
                continue
            for name, chapters in names.items():
                for chapter, traits in chapters.items():
                    if not isinstance(traits, dict):
                        self._reshaped_data[attribute][name][chapter] = traits
                    for trait, detail in traits.items():
                        self._reshaped_data[attribute][name][trait][
                            chapter
                        ] = detail
        return self._reshaped_data


class SortDictionary(CleanData):
    """
    Sorts the keys of a nested dictionary.

    Args:
        binder (dict): The dictionary to be sorted.

    Methods:
    - __call__: Calls the _sort method and returns the sorted dictionary.
    - _sort: Sorts the keys of a nested dictionary in ascending order.

    Returns:
        dict: A dictionary with the same structure as self.binder, but
        with the keys sorted in ascending order.
    """

    def __call__(self) -> dict:
        return self._sort(self.binder)

    def _sort(self, binder: dict) -> dict:
        """
        Sorts the keys of a nested dictionary.

        Returns:
            dict: A dictionary with the same structure as self.binder, but
            with the keys sorted in ascending order.
        """

        sorted_dict = {}
        for outer_key, nested_dict in binder.items():
            middle_dict = {
                key: nested_dict[key] for key in sorted(nested_dict)
            }
            for key, inner_dict in middle_dict.items():
                if isinstance(inner_dict, dict) and all(
                    isinstance(key, int) for key in inner_dict.keys()
                ):
                    sorted_inner_dict = {
                        str(inner_key): inner_dict[str(inner_key)]
                        for inner_key in sorted(map(int, inner_dict.keys()))
                    }
                    middle_dict[key] = sorted_inner_dict
                else:
                    raise KeyError(
                        "Dictionary level should be chapter numbers"
                        f"but was {inner_dict.keys()}"
                    )
            sorted_dict[outer_key] = middle_dict
        return sorted_dict


class ReplaceNarrator(CleanData):
    """
    A class that replaces occurrences of the word 'narrator', 'protagonist',
    'the main character', or 'main character' with a specified narrator name
    in a given dictionary.

    Args:
        binder (dict): The dictionary to be cleaned.

    Attributes:
        _binder (dict): The dictionary to be cleaned.
        _narrator_name (str): The name of the narrator to replace the
            occurrences with.

    Methods:
        _replace_str(self, value: str) -> str:
            Replaces the occurrences of the words in a string with the
                narrator name.

        _clean_dict(self, value: dict) -> dict:
            Recursively replaces the occurrences of the words in a dictionary
                with the narrator name.

        _clean_list(self, value: list) -> list:
            Recursively replaces the occurrences of the words in a list with
                the narrator name.

        replace(self, narrator_name: str) -> dict:
            Replaces the occurrences of the words in the specified dictionary
                with the narrator name.
    """

    def _replace_str(self, value: str) -> str:
        narrator_list: str = (
            r"\b(narrator|protagonist|the main character|main character)\b"
        )
        return re.sub(narrator_list, self._narrator_name, value)

    def _clean_dict(self, value: dict) -> dict:
        new_dict: dict = {}
        for key, val in value.items():
            cleaned_key = self._replace_str(key)
            new_dict[cleaned_key] = self._clean_dict(val)
        return new_dict

    def _clean_list(self, value: list) -> list:
        return [self._replace_str(val) for val in value]

    def _handle_value(self, value: Union[dict, list, str]):
        type_handlers: Dict[type, Callable] = {
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
        """
        Replaces the word narrator, protagonist and synonyms with the
        character's name
        """
        self._narrator_name = narrator_name
        return self._clean_dict(self.binder)


def clean_lorebinders(lorebinder: dict, narrator: str):
    reshaper = ReshapeDict(lorebinder)
    reshaped: dict = reshaper.reshaped

    remove_none = RemoveNoneFound(reshaped)
    only_found: dict = remove_none.clean_none_found()

    deduplicator = DeduplicateKeys(only_found)
    deduped: dict = deduplicator.deduplicated

    replace_narrator = ReplaceNarrator(deduped)
    narrator_replaced: dict = replace_narrator.replace(narrator)
    return SortDictionary(narrator_replaced)
