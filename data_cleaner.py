import re

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
    
