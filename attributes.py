class AttributeExtractor:
    """
    Responsible for extracting characters, settings, and other attributes from
    the chapter text using Named Entity Recognition (NER).
    """
    def extract_attributes(self, chapter):
        """
        Takes a Chapter object and extracts the attributes using the OpenAI
        API. Returns a nested dictionary structure with the extracted data.
        """


class AttributeAnalyzer:
    """
    Responsible for analyzing the extracted attributes to gather detailed
    information, such as descriptions, relationships, and locations.
    """
    def analyze_attributes(self, extracted_data):
        """
        Takes the nested dictionary from AttributeExtractor and analyzes the
        extracted attributes using an AI API.
        Updates the nested dictionary with the analyzed data.
        """


class AttributeSummarizer:
    """
    Responsible for generating summaries for each attribute across all
    chapters.
    """
    def summarize_attributes(self, reshaped_data):
        """
        Takes the reshaped nested dictionary from DataReshaper and generates
        summaries for attributes using an AI API.
        Updates the nested dictionary with the summaries.
        """