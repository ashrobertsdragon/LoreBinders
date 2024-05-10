class DataCleaner:
    """
    Responsible for cleaning the extracted and analyzed data.
    """
    def remove_none_entries(self, analyzed_data):
        """
        Takes the nested dictionary from AttributeAnalyzer and removes "None found" entries.
        Returns the cleaned nested dictionary.
        """

    def deduplicate_keys(self, cleaned_data):
        """
        Takes the cleaned nested dictionary and deduplicates keys.
        Returns the updated nested dictionary.
        """

    def replace_placeholders(self, deduped_data):
        """
        Takes the deduped nested dictionary and replaces placeholders (e.g., "narrator") with actual names.
        Returns the updated nested dictionary.
        """

    def reshape_data(self, cleaned_data):
        """
        Takes the cleaned nested dictionary from DataCleaner and reshapes the data structure.
        Returns the reshaped nested dictionary.
        """