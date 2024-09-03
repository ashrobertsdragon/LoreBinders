from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from ebook2text.convert_file import convert_file  # type: ignore

if TYPE_CHECKING:
    from lorebinders._type_annotations import AIProviderManager

import lorebinders.data_cleaner as data_cleaner
import lorebinders.make_pdf as make_pdf
from lorebinders._managers import RateLimitManager
from lorebinders._types import InstructionType
from lorebinders.ai.ai_interface import AIInterface, AIModelConfig
from lorebinders.ai.ai_models._model_schema import AIModelRegistry, APIProvider
from lorebinders.ai.ai_models.json_file_model_handler import (
    JSONFileProviderHandler
)
from lorebinders.ai.rate_limiters.file_rate_limit_handler import (
    FileRateLimitHandler
)
from lorebinders.book import Book, Chapter
from lorebinders.book_dict import BookDict
from lorebinders.name_tools import (
    name_analyzer,
    name_extractor,
    name_summarizer
)


def create_book(book_dict: BookDict) -> Book:
    return Book(book_dict)


def perform_ner(
    ai: AIInterface,
    metadata: BookDict,
    chapter: Chapter,
) -> None:
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
    return name_summarizer.summarize_names(ai, binder)


def initialize_ai(
    provider: APIProvider, family: str, model_id: int, rate_limiter
) -> AIInterface:
    ai_config = AIModelConfig(provider)
    ai = ai_config.initialize_api(rate_limiter)
    ai.set_family(ai_config, family)
    ai.set_model(model_id)
    return ai


def initializer_ner(
    provider: APIProvider, rate_limiter: RateLimitManager
) -> AIInterface:
    return initialize_ai(
        provider=provider,
        family="openai",
        model_id=1,
        rate_limiter=rate_limiter,
    )


def initializer_analyzer(
    provider: APIProvider, rate_limiter: RateLimitManager
) -> AIInterface:
    return initialize_ai(
        provider=provider,
        family="openai",
        model_id=2,
        rate_limiter=rate_limiter,
    )


def initializer_summarizer(
    provider: APIProvider, rate_limiter: RateLimitManager
) -> AIInterface:
    return initialize_ai(
        provider=provider,
        family="openai",
        model_id=1,
        rate_limiter=rate_limiter,
    )


def build_binder(
    ner: AIInterface, analyzer: AIInterface, metadata: BookDict, book: Book
) -> None:
    for chapter in book.chapters:
        perform_ner(ner, book.metadata, chapter)
        analysis = analyze_names(analyzer, metadata, chapter)
        book.build_binder(chapter.number, analysis)
    data_cleaner.clean_lorebinders(book.binder, metadata.narrator or "")


def summarize(ai: AIInterface, book: Book) -> None:
    binder = summarize_names(ai, book.binder)
    book.update_binder(binder)


def create_folder(folder: str, base_dir: str) -> Path:
    created_path = Path(base_dir) / folder
    created_path.mkdir(parents=True, exist_ok=True)
    return created_path


def create_user(author: str) -> str:
    names = author.split(" ")
    return "_".join(names)


def create_user_folder(author: str, work_dir: str) -> Path:
    user = create_user(author)
    return create_folder(user, work_dir)


def add_txt_filename(book_dict: BookDict, book_file: str) -> None:
    base, _ = os.path.splitext(book_file)
    txt_filename = f"{base}.txt"
    book_dict.txt_file = txt_filename


def convert(file_path: Path, limited_metadata: dict) -> None:
    convert_file(file_path, limited_metadata)


def create_limited_metadata(book_dict: BookDict) -> dict:
    author = book_dict.author
    title = book_dict.title
    return {"title": title, "author": author}


def convert_book_file(book_dict: BookDict, work_dir: str) -> None:
    book_file = book_dict.book_file
    author = book_dict.author

    user_folder: Path = create_user_folder(author, work_dir)
    file_path: Path = user_folder / book_file
    limited_metadata: dict = create_limited_metadata(book_dict)
    convert(file_path, limited_metadata)
    add_txt_filename(book_dict, book_file)


def initialize_ai_model_registry(
    provider_registry: type[AIProviderManager], *args, **kwargs
) -> AIModelRegistry:
    """
    Initializes and returns an AIModelRegistry from the provided handler.

    Args:
        provider_registry (AIProviderManager subclass): An uninitialized
        concrete subclass of the AIProviderManager abstract class.
        args: Any positional arguments that need to be passed to the provider
        class at initialization.
        kwargs: Any keyword arguments that need to be passed to the provider
        class at initialization.

    Returns:
        AIModelRegistry: A dataclass containing a list of all the provider
        classes in the data file/database.
    """
    handler = provider_registry(*args, **kwargs)
    return handler.registry


def start(book_dict: BookDict, work_base_dir: str) -> None:
    convert_book_file(book_dict, work_base_dir)

    book = create_book(book_dict)

    ai_registry = initialize_ai_model_registry(
        JSONFileProviderHandler, "json_files"
    )
    provider = ai_registry.get_provider("OpenAI")
    rate_handler = FileRateLimitHandler()

    ner = initializer_ner(provider, rate_handler)
    analyzer = initializer_analyzer(provider, rate_handler)
    summarizer = initializer_summarizer(provider, rate_handler)

    build_binder(ner, analyzer, book_dict, book)
    summarize(summarizer, book)
    data_cleaner.final_reshape(book.binder)

    if book_dict.user_folder is not None:
        make_pdf.create_pdf(book)
