from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._type_annotations import (
        BookDict,
        Chapter,
    )

import lorebinders.data_cleaner as data_cleaner
import lorebinders.make_pdf as make_pdf
import lorebinders.start_ai_initialization as start_ai_initialization
from lorebinders._types import InstructionType
from lorebinders.ai.ai_interface import AIInterface
from lorebinders.ai.ai_models.json_file_model_handler import (
    JSONFileProviderHandler,
)
from lorebinders.ai.rate_limiters.file_rate_limit_handler import (
    FileRateLimitHandler,
)
from lorebinders.book import Book
from lorebinders.convert_book_file import convert_book_file
from lorebinders.name_tools import (
    name_analyzer,
    name_extractor,
    name_summarizer,
)


def create_book(book_dict: BookDict) -> Book:
    """Create a Book object from BookDict metadata.

    Args:
        book_dict: Configuration object containing book metadata.

    Returns:
        A Book object initialized with the provided metadata.
    """
    return Book(book_dict)


def perform_ner(
    ai: AIInterface,
    metadata: BookDict,
    chapter: Chapter,
) -> None:
    """Perform named entity recognition on a chapter.

    Args:
        ai: AI interface for making API calls.
        metadata: Book metadata containing configuration options.
        chapter: Chapter object to extract names from.
    """
    role_script = name_extractor.build_role_script(metadata.custom_categories)
    names = name_extractor.extract_names(
        ai, chapter, role_script, metadata.narrator
    )
    chapter.add_names(names)


def analyze_names(
    ai: AIInterface,
    metadata: BookDict,
    chapter: Chapter,
) -> dict:
    """Analyze extracted names to generate character analysis.

    Args:
        ai: AI interface for making API calls.
        metadata: Book metadata containing configuration options.
        chapter: Chapter object containing extracted names.

    Returns:
        Dictionary containing the analysis results.
    """
    absolute_max_tokens = ai.model.absolute_max_tokens
    instruction_type = InstructionType("markdown")
    helper = name_analyzer.initialize_helpers(
        instruction_type=instruction_type,
        absolute_max_tokens=absolute_max_tokens,
        added_character_traits=metadata.character_traits,
    )

    role_scripts = name_analyzer.build_role_scripts(
        chapter.names, helper, instruction_type
    )
    analysis = name_analyzer.analyze_names(
        ai, instruction_type, role_scripts, chapter
    )
    chapter.add_analysis(analysis)
    return analysis


def summarize_names(
    ai: AIInterface,
    binder: dict,
) -> dict:
    """Summarize names across all chapters.

    Args:
        ai: AI interface for making API calls.
        binder: Dictionary containing character analysis data.

    Returns:
        Dictionary containing summarized character information.
    """
    return name_summarizer.summarize_names(ai, binder)


def build_binder(
    ner: AIInterface, analyzer: AIInterface, metadata: BookDict, book: Book
) -> None:
    """Build the complete character analysis binder for a book.

    Args:
        ner: AI interface for named entity recognition.
        analyzer: AI interface for character analysis.
        metadata: Book metadata containing configuration options.
        book: Book object to process.
    """
    for chapter in book.chapters:
        perform_ner(ner, book.metadata, chapter)
        analysis = analyze_names(analyzer, metadata, chapter)
        book.build_binder(chapter.number, analysis)
    data_cleaner.clean_lorebinders(book.binder, metadata.narrator or "")


def summarize(ai: AIInterface, book: Book) -> None:
    """Summarize character information across all chapters.

    Args:
        ai: AI interface for making API calls.
        book: Book object containing the binder to summarize.
    """
    binder = summarize_names(ai, book.binder)
    book.update_binder(binder)


def start(book_dict: BookDict, work_base_dir: str) -> None:
    """Start the complete lorebinder creation process.

    Args:
        book_dict: Configuration object containing book metadata.
        work_base_dir: Base directory for output files.
    """
    convert_book_file(book_dict, work_base_dir)

    book = create_book(book_dict)

    ai_registry = start_ai_initialization.initialize_ai_model_registry(
        JSONFileProviderHandler, "json_files"
    )
    provider = ai_registry.get_provider("OpenAI")
    rate_handler = FileRateLimitHandler()

    ner = start_ai_initialization.initialize_ner(provider, rate_handler)
    analyzer = start_ai_initialization.initialize_analyzer(
        provider, rate_handler
    )
    summarizer = start_ai_initialization.initialize_summarizer(
        provider, rate_handler
    )

    build_binder(ner, analyzer, book_dict, book)
    summarize(summarizer, book)
    data_cleaner.final_reshape(book.binder)

    if book_dict.user_folder is not None:
        make_pdf.create_pdf(book)
