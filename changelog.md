# Changelog

## 05-31-2025

- Updated json_tools to import os and use os.path.exists() for JSON file validation.
- Added default values for max_output_tokens and generation in Pydantic Model schema.
- Adjusted replace_model in sql_provider_handler to unpack all returned attributes including new defaults.
- Modified make_pdf to use after_section.value and convert output_path to str for ReportLab compatibility.
- Corrected project name capitalization to LoreBinder in PDF title page and corresponding tests.
- Introduced binder and mock_compare_names fixtures and corrected integration test signatures for PDF and name sorting tests.
- Fixed test_remove_none_found by adding missing sample_lorebinder parameter
- Fixed test_deduplicate_keys by correcting DeduplicateKeys instantiation and test assertions
- Fixed test_create_detail_list_non_integer_keys by adding ValueError validation for non-digit chapter keys
- Fixed test_add_item_to_story_adds_multiple_flowables by correcting mock to properly simulate enum with .value attribute

## 06-01-2025

- Fixed file handling tests by patching pathlib instead of builtin open.
- Fixed mocks for make_pdf unit tests.

## 06-02-2025

- Ignore type for config lookups that decouple annotates as `bool | Any` in smtp_handler.SMTPHandler.
- Fixed failing tests for SMTPHandler by replacing mocks for pathlib.

## 06-04-2025

- Fixed failing tests for `name_tools` module by replacing mocks for pathlib.
