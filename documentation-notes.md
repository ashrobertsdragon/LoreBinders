# Documentation Notes

## DeduplicateKeys

### deduplicate method

- If nested_dict is not a dictionary, add key-value pair to new dictionary
- Use combinations to get a generator iterable of two-key combinations of the middle dictionary keys
- Check if any individual key has been checked already
- Check if two keys are similar with boolean method
- Use prioritize_keys to provide sorted order to keys (plural, singular usually)
- Use merge_values to combine values of keys
add key that values merged from to duplicate_keys set to be skipped in future iterations
- create new inner dictionary with keys that are not in duplicate_keys set
add key-inner dictionary value to new dictionary

### `_is_similar_key`

when value1 is a list and value2 is a dictionary, use `ChainMap` to merge the dictionary in value2 with any dictionaries in the list of value1, otherwise, just add the item to the new list. when done, check if the keys of the value2 dictionary are in the list, and if no, you can go in the list

## File Handling and Test Utilities Updates

- Restored use of Path.open() in file_handling module for reading and writing files to align with pathlib guidelines and enable mocking via Path.open.
- Updated json_tools to use pathlib.Path.exists() for reliable JSON file existence checks.
- Provided default values for Pydantic Model schema fields (`max_output_tokens`, `generation`) to prevent missing argument errors in SQL provider tests.
- Adjusted replace_model tuple unpacking in sql_provider_handler to include new default attributes.
- Modified make_pdf to append after_section.value and convert output_path to str for compatibility with ReportLab APIs.
- Corrected `LoreBinder` capitalization in title page creation and updated related integration test assertions.
- Added `binder` and `mock_compare_names` fixtures and fixed integration test signatures to properly include temp_output_path fixture.

## make_pdf

- In the add_content method, using `# type: ignore` for `ListFlowable(detail_list)`. Type checking believes that `detail_list` of type `ListItem` is not a subtype of `_NestedFlowable`. But the ListFlowable class's iterflowable method explicitly checks for ListItem, so it is a compatible type.
