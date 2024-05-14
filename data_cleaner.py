import re
from typing import Union, Tuple

from abc import ABC

from _titles import TITLES

class Data(ABC):
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
        name_split: str = name.split()
        if name_split[0] in TITLES and name not in TITLES:
            return " ".join(name_split[1:])

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
        patterns = {
            r'(\w+)(ves)$': r'\1f',
            r'(\w+)(ies)$': r'\1y',
            r'(\w+)(i)$': r'\1us',
            r'(\w+)(a)$': r'\1um',
            r'(\w+)(en)$': r'\1an',
            r'(\w+)(oes)$': r'\1o',
            r'(\w+)(ses)$': r'\1s',
            r'(\w+)(hes)$': r'\1h',
            r'(\w+)(xes)$': r'\1x',
            r'(\w+)(zes)$': r'\1z'
        }

        for pattern, repl in patterns.items():
            singular = re.sub(pattern, repl, plural)
            if plural != singular:
                return singular
        return plural[:-1]

class CleanData(Data):
    def __init__(self):
        self.lorebinder = self.book.get_lorebinder()
class RemoveNoneFound(CleanData):

    def __call__(self, d: Union[dict|list|str]) -> Union[dict|list|str]:
        return self._remove_none(d)

    def _remove_none(self, d: Union[dict|list|str]) -> Union[dict|list|str]:
        """
        Takes the nested dictionary from AttributeAnalyzer and removes "None found" entries.
        Returns the cleaned nested dictionary.
        """
        if isinstance(d, dict):
            new_dict = {}
            for key, value in d.items():
                cleaned_value = self._remove_none(value)
                if not isinstance(cleaned_value, list) and cleaned_value != "None found":
                    new_dict[key] = cleaned_value
                    continue
                elif isinstance(cleaned_value, list):
                    if len(cleaned_value) > 1:
                        new_dict[key] = cleaned_value
                    elif len(cleaned_value) == 1:
                        new_dict[key] = cleaned_value[0]
                        return new_dict
        elif isinstance(d, list):
            new_list = []
            for item in d:
                cleaned_item = self.remove_none_found(item)
                if cleaned_item != "None found":
                    new_list.append(cleaned_item)
                    return new_list
        else:
            return "" if d == "None Found" else d

class DeduplicateKeys(CleanData):
    def __call__(self, d: dict) -> dict:
        return self._deduplicate_keys(d)
    def _deduplicate_keys(self, d: dict) -> dict:
        """
        Removes duplicate keys in a dictionary by merging singular and plural forms of keys.

        Args:
            dictionary: The dictionary to deduplicate.
        
        Returns the deduplicated dictionary.
        """

        cleaned_dict = {}

        for outer_key, nested_dict in d.items():
            if not isinstance(nested_dict, dict):
                continue
            duplicate_keys = []
            inner_dict = {}

            for key1 in nested_dict:
                if key1 in duplicate_keys:
                    continue
                for key2 in nested_dict:
                    if key2 in duplicate_keys or key1 == key2:
                        continue
                    if self._is_similar_key(key1, key2):
                        key_to_merge, key_to_keep = self._prioritize_keys(key1, key2)
                        nested_dict[key_to_keep] = self._merge_values(nested_dict[key_to_keep], nested_dict[key_to_merge])
                        duplicate_keys.append(key_to_merge)

            for key, value in nested_dict.items():
                if key in duplicate_keys:
                    continue
                inner_dict[key] = value
            cleaned_dict[outer_key] = inner_dict
        return self._deduplicate_across_dictionaries(cleaned_dict)
    
    def _prioritize_keys(self, key1: str, key2: str) -> Tuple[str, str]:
        "Determines priority of keys, based on whether one is standalone title or length"
        "Order is lower priority, higher priority"

        key1_is_title = self.is_title(key1)
        key2_is_title = self.is_title(key2)
        lower_key1 = key1.lower()
        lower_key2 = key2.lower()

        if (lower_key1 in lower_key2 or lower_key2 in lower_key1) and lower_key1 != lower_key2:
            if key1_is_title:
                return key2, key1
            if key2_is_title:
                return key1, key2
        return sorted([key1, key2], key = len)

    def _is_similar_key(self, key1: str, key2: str) -> bool:
        "Determines if two keys are similar"
        manipulate_data = ManipulateData()
        detitled_key1 = manipulate_data.remove_titles(key1)
        detitled_key2 = manipulate_data.remove_titles(key2)
        singular_key1 = manipulate_data.to_singular(key1)
        singular_key2 = manipulate_data.to_singular(key2)

        if (
                key1 + " " in key2
                or key2 + " " in key1
                or key1 == singular_key2
                or singular_key1 == key2
        ):
            return True

        key1_is_title = self._is_title(key1)
        key2_is_title = self._is_title(key2)
        if key1_is_title and key1.lower() in key2.lower():
            return True
        if key2_is_title and key2.lower() in key1.lower():
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

    def _is_title(self, key: str) -> bool:
        return key.lower() in TITLES

    def _deduplicate_across_dictionaries(self, attribute_summaries: dict) -> dict:
        "Finds dupicates across dictionaries"

        characters_dict = attribute_summaries.get("Characters", {})

        for attribute, names in attribute_summaries.items():
            if attribute == "Characters":
                continue
            for name in list(names.keys()):
                if name not in characters_dict:
                    continue
                for chapter, details in names[name].items():
                    if chapter in characters_dict[name]:
                        merged_values = self._merge_values(characters_dict[name][chapter], details)
                        attribute_summaries["Characters"][name][chapter] = merged_values
                    elif isinstance(details, dict):
                        attribute_summaries["Characters"][name][chapter] = details
                    else:
                        attribute_summaries["Characters"][name][chapter] ={"Also": details}
                del names[name]

        return attribute_summaries

    def _merge_values(self, value1: Union[dict|list|str], value2: Union[dict|list|str]) -> Union[dict|list|str]:
        """
        Merges two dictionary key values of unknown datatypes into one
        Arguments:
            value1: A dictionary key value
            value2: A dictionary key value

        Returns merged dictionary key value
        """

        if isinstance(value1, dict) and isinstance(value2, dict):
            for k, v in value2.items():
                if k in value1:
                    value1[k] = self._merge_values(value1[k], v)
                else:
                    value1[k] = v    
        elif isinstance(value1, list) and isinstance(value2, list):
            value1.extend(value2)
        elif isinstance(value1, list) and isinstance(value2, dict):
            for k, v in value2.items():
                if k in value1:
                    value1[k] = self._merge_values(value1[k], v)
                else:
                    value1.append({k: v})
        elif isinstance(value1, dict) and isinstance(value2, list):
            if "Also" in value1:
                value1["Also"].extend(value2)
            else:
                value1["Also"] = value2
        elif isinstance(value1, dict):
            for key in value1:
                if key == value2:
                    return value1
            value1["Also"] = value2
        elif isinstance(value2, list):
            value2.append(value1)
            return value2
        else:
            return [value1, value2]
        return value1

class ReshapeDict(CleanData): 
    def __call__(self) -> None:
        self._reshape()

    def _reshape(self) -> dict:
        """
        Reshapes a dictionary of chapter summaries to demote chapter numbers inside attribute names.

        Args:
            chapter_summaries: Dictionary containing chapter summaries.
        
        Returns a reshaped dictionary.
        """

        reshaped_data = {}

        for chapter, chapter_data in self.lorebinder.items():
            for cateogory, cateogory_data in chapter_data.items():
                cateogory = cateogory.title()
                if cateogory not in reshaped_data:
                    reshaped_data[cateogory] = {}
                for name, name_details in cateogory_data.items():
                    if isinstance(name_details, dict):
                        for key, value in name_details.items():
                            reshaped_data[cateogory].setdefault(name, {}).setdefault(chapter, {}).setdefault(key, []).append(value)
                    elif isinstance(name_details, str):
                        reshaped_data[cateogory].setdefault(name, {}).setdefault(chapter, []).append(name_details)
        self.book.update_lorebinder(reshaped_data)

class FinalReshape(ReshapeDict):

    def _reshape(self) -> None:
        """
        Demotes chapter numbers to lowest dictionary in Characters and Settings dictionaries.
        
        Argument:
        folder_name: A string containing the path to the folder containing the chapter summaries.
        """

        reshaped_data = {}
        for attribute, names in self.lorebinder.items():
            if attribute not in ["Characters", "Settings"]:
                reshaped_data[attribute] = names
                continue
            reshaped_data[attribute] = {}
            for name, chapters in names.items():
                reshaped_data[attribute][name] = {}
                for chapter, traits in chapters.items():
                    if not isinstance(traits, dict):
                        reshaped_data[attribute][name][chapter] = traits
                        continue
                    for trait, detail in traits.items():
                        if trait not in reshaped_data[attribute][name]:
                            reshaped_data[attribute][name][trait] = {}
                        reshaped_data[attribute][name][trait][chapter] = detail
        self.book.update_lorebinder(reshaped_data)

class SortDictionary(CleanData):
    def __call__(self) -> None:
        self._sort()
    
    def _sort(self) -> None:
        "Sorts dictionary keys"

        sorted_dict = {}
        for outer_key, nested_dict in self.lorebinder.items():
            middle_dict = {key: nested_dict[key] for key in sorted(nested_dict)}
            for key, inner_dict in middle_dict.items():
                if isinstance(inner_dict, dict):
                    sorted_inner_dict = {str(inner_key): inner_dict[str(inner_key)]
                                                            for inner_key in sorted(map(int, inner_dict.keys()))}
                    middle_dict[key] = sorted_inner_dict
            sorted_dict[outer_key] = middle_dict

        self.book.update_lorebinder(sorted_dict)

class ReplaceNarrator(CleanData):
    def __init__(self, narrator_name: str) -> None:
        super().__init__()
        self._narrator_list: list = ["narrator", "protagonist", "the main character", "main character"]
        self._narrator_name: str = narrator_name
    
    def __call__(self, narrator_name: str) -> None:
        self._replace(narrator_name)

    def _iterate_narrator_list(self, value: str) -> str:
        for narrator in self._narrator_list:
            new_value: str = value.replace(narrator, self._narrator_name)
        return new_value
    
    def _replace(self, narrator_name: str) -> None:
        "Replaces the word narrator, protagonist and synonyms with the chracter's name"

        new_dict = {}
        for key, value in self._lorebinder.items():
            if key in self._narrator_list:
                new_dict[narrator_name] = value
            if isinstance(value, dict):
                new_dict[key] = self._clean(value, narrator_name)
            elif isinstance(value, str):
                new_dict[key] = self._iterate_narrator_list(value)
            elif isinstance(value, list):
                new_dict[key] = [self._iterate_narrator_list(val) for val in value]
            else:
                new_dict[key] = value # any other data type will not match a string
        self.book.update_lorebinder(new_dict)

def clean_lorebinders(narrator: str):
    ReshapeDict()
    RemoveNoneFound()
    DeduplicateKeys()
    ReplaceNarrator(narrator)
    SortDictionary()
