from lorebinders.ai.ai_interface import AIInterface
from lorebinders.name_tools.name_tools import NameTools
from lorebinders.prompt_generator import create_prompts
from lorebinders.role_script import RoleScript


class NameSummarizer(NameTools):
    """
    Responsible for generating summaries for each name across all
    chapters.

    Attributes:
        _ai (AIInterface): The AIInterface object.
        _categories_base (list): The base list of categories to be analyzed.
        temperature (float): The temperature parameter for AI response
            generation.
        max_tokens (int): The maximum number of tokens for AI response
            generation.
        _single_role_script (str): The role script to be used for AI response
            generation.
        lorebinder (dict): The lorebinder dictionary containing the names,
            categories, and summaries.

    Methods:
        __init__: Initialize the NameSummarizer class with an AIInterface
            object.

        summarize_names: Generate summaries for each name in the lorebinder.

        _parse_response: Parse the AI response and update the lorebinder with
            the generated summary.
    """

    def __init__(self, ai: AIInterface) -> None:
        """
        Initialize the NameSummarizer class with an AI Interface object.

        Args:
            ai (AIInterface): The AIInterface object.

        Attributes:
            temperature (float): The temperature parameter for AI response
                generation.
            max_tokens (int): The maximum number of tokens for AI response
                generation.
            _single_role_script (str): The role script to be used for AI
                response generation.
            _current_category (str): The current category being analyzed.
            _current_name (str): The current name being analyzed.
            _lorebinder (dict): The lorebinder dictionary containing the names,
                categories, and summaries.
        """

        super().__init__(ai)

        self.temperature: float = 0.4
        self.max_tokens: int = 200

        self._single_role_script: RoleScript | None = None
        self._current_category: str | None = None
        self._current_name: str | None = None
        self.lorebinder: dict = {}

    def build_role_script(self) -> None:
        system_message = (
            "You are an expert summarizer. Please summarize the description "
            "over the course of the story for the following:"
        )
        self._single_role_script = RoleScript(system_message, self.max_tokens)

    def summarize_names(self, lorebinder: dict) -> dict:
        """
        Generate summaries for each name in the Lorebinder.

        This method iterates over each name in the Lorebinder and generates a
        summary. The generated summary is then parsed and updated in the
        Lorebinder dictionary.
        """
        self.lorebinder = lorebinder
        for category, name, prompt in create_prompts(lorebinder):
            self._current_category = category
            self._current_name = name
            if self._single_role_script:
                response = self._get_ai_response(
                    self._single_role_script, prompt
                )
                self.lorebinder = self._parse_response(response)
        return self.lorebinder

    def _parse_response(self, response: str) -> dict:
        """
        Parse the AI response and update the lorebinder with the generated
        summary.

        This method takes the AI response as input and updates the lorebinder
        dictionary with the generated summary for a specific category and
        name. If the response is not empty, the summary is assigned to the
        corresponding category and name in the lorebinder.

        Args:
            category (str): The category of the name.
            name (str): The name for which the summary is generated.
            response (str): The AI response containing the generated summary.
        """
        if response and self._current_category and self._current_name:
            category = self._current_category
            name = self._current_name
            self.lorebinder[category][name] = {"summary": response}
        return self.lorebinder
