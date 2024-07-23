from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._types import BookDict, Chapter

from lorebinders.ai.ai_interface import AIInterface
from lorebinders.name_tools import NameTools
from lorebinders.role_script import RoleScript
from lorebinders.sort_names import SortNames


class NameExtractor(NameTools):
    """
    Responsible for extracting characters, settings, and other categories from
    the chapter text using Named Entity Recognition (NER).
    """

    def __init__(self, ai: AIInterface) -> None:
        super().__init__(ai)

        self.max_tokens: int = 1000
        self.temperature: float = 0.2

    def initialize_chapter(self, metadata: BookDict, chapter: Chapter) -> None:
        self.metadata = metadata
        self.chapter = chapter
        self._prompt = f"Text: {self.chapter.text}"
        self.narrator = self.metadata.narrator
        self.custom_categories = self.metadata.custom_categories
        self._base_instructions, self._further_instructions = (
            self._create_instructions()
        )

    def _create_instructions(self) -> tuple[str, str]:
        # TODO: Pass in instructions file path from config?
        base_instruction = self._get_instruction_text(
            "name_extractor_sys_prompt.txt"
        )
        further_instructions = self._get_instruction_text(
            "name_extractor_instructions.txt"
        )
        return base_instruction, further_instructions

    def _build_custom_role(self) -> str:
        """
        Builds a custom role script based on the custom categories provided.

        Returns:
            str: The custom role script.

        """
        role_categories: str = ""
        if self.custom_categories and len(self.custom_categories) > 0:
            name_strings: list = []
            for name in self.custom_categories:
                attr: str = name.strip()
                name_string: str = f"{attr}:{attr}1, {attr}2, {attr}3"
                name_strings.append(name_string)
                role_categories = "\n".join(name_strings)
        return role_categories

    def build_role_script(self) -> None:
        """
        Builds the role script for the NameExtractor class.

        This method constructs the role script that will be used by the
        NameExtractor class to extract characters and settings from the
        chapter text. The role script includes instructions for the AI, such
        as identifying characters and settings, handling first-person scenes,
        and formatting the output.

        Returns:
            None
        """
        role_categories: str = self._build_custom_role()

        system_message = (
            f"{self._base_instructions}\n{self.custom_categories}.\n"
            f"{self._further_instructions}\n{role_categories}"
        )
        self._single_role_script = RoleScript(system_message, self.max_tokens)

    def extract_names(self) -> dict:
        response = self._get_ai_response(
            self._single_role_script, self._prompt
        )
        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict:
        """
        Parses the response from the AI model to extract names and add them to
        the Chapter object.

        This method takes the response from the AI model as input and extracts
        the names using the _sort_names method. It also retrieves the narrator
        from the Book object. The extracted names are then added to the
        Chapter object using the add_names method.

        Args:
            response (str): The response from the AI model.

        Returns:
            dict: A dictionary containing the extracted names.
        """
        sorter = SortNames(response, self.narrator or "")
        return sorter.sort()
