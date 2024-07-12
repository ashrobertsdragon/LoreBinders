from __future__ import annotations

from typing import TYPE_CHECKING

from lorebinders.ai.ai_models._model_schema import APIProvider

if TYPE_CHECKING:
    from lorebinders._types import Book, BookDict, Chapter

from lorebinders.attributes import NameAnalyzer, NameExtractor, NameSummarizer
from lorebinders.file_handling import write_json_file


class Binder:
    """
    Class representing the book analysis binder.
    """

    def __init__(self, book: Book, ai_model: APIProvider) -> None:
        self.book = book
        self.ai_models = ai_model
        self.binder_type = __name__.lower()
        self._book_name: str | None = None
        self._temp_file: str | None = None

    def __str__(self) -> str:
        return f"Binder for {self.book_name} - {self.book.author}"

    @property
    def book_name(self) -> str:
        if self._book_name is None:
            self._book_name = self.book.name
        return self._book_name

    @property
    def metadata(self) -> BookDict:
        return self.book.metadata

    @property
    def binder_tempfile(self) -> str:
        if self._temp_file is None:
            self._temp_file = f"{self.book_name}-{self.binder_type}.json"
        return self._temp_file

    def add_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        self._binder = binder
        write_json_file(self._binder, self.binder_tempfile)

    def update_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        if self._binder != binder:
            self.add_binder(binder)

    @property
    def binder(self) -> dict:
        return self._binder

    def perform_ner(
        self, ner: NameExtractor, metadata: BookDict, chapter: Chapter
    ) -> None:
        ner.initialize_chapter(metadata, chapter)
        ner.build_role_script()
        names = ner.extract_names()
        chapter.add_names(names)

    def analyze_names(
        self, analyzer: NameAnalyzer, metadata: BookDict, chapter: Chapter
    ) -> None:
        analyzer.initialize_chapter(metadata, chapter)
        analyzer.build_role_script()
        analysis = analyzer.analyze_names()
        chapter.add_analysis(analysis)

    def summarize(self, summarizer: NameSummarizer) -> None:
        summarizer.build_role_script()
        self._binder = summarizer.summarize_names(self._binder)

    def build_binder(self) -> None:
        ner = NameExtractor(self.ai_models)
        analyzer = NameAnalyzer(self.ai_models)
        summarizer = NameSummarizer(self.ai_models)

        for chapter in self.book.chapters:
            self.perform_ner(ner, self.metadata, chapter)
            self.analyze_names(analyzer, self.metadata, chapter)
        self.summarize(summarizer)
