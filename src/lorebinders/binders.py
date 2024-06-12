from typing import Optional

from _types import AIModels, Book, BookDict, Chapter
from attributes import NameAnalyzer, NameExtractor, NameSummarizer
from file_handling import write_json_file


class Binder:
    """
    Base class for all book analysis binders.
    """

    def __init__(self, book: Book, ai_model: AIModels) -> None:
        self.book = book
        self.ai_models = ai_model
        self.binder_type = __name__.lower()
        self._book_name: Optional[str] = None
        self._temp_file: Optional[str] = None

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
        write_json_file(self._binder, self._temp_file)

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
