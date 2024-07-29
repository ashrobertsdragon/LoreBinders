from __future__ import annotations

import os
from typing import TYPE_CHECKING

from ebook2text.convert_file import convert_file  # type: ignore

if TYPE_CHECKING:
    from lorebinders._type_annotations import AIProviderManager

import lorebinders.make_pdf as make_pdf
from lorebinders._managers import RateLimitManager
from lorebinders.ai.ai_interface import AIInterface, AIModelConfig
from lorebinders.ai.ai_models._model_schema import AIModelRegistry, APIProvider
from lorebinders.ai.ai_models.json_file_model_handler import (
    JSONFileProviderHandler
)
from lorebinders.ai.rate_limiters.file_rate_limit_handler import (
    FileRateLimitHandler
)
from lorebinders.attributes import NameAnalyzer, NameExtractor, NameSummarizer
from lorebinders.book import Book, Chapter
from lorebinders.book_dict import BookDict


def create_book(book_dict: BookDict) -> Book:
    return Book(book_dict)


def perform_ner(
    ner: NameExtractor,
    metadata: BookDict,
    chapter: Chapter,
) -> None:
    ner.initialize_chapter(metadata, chapter)
    ner.build_role_script()
    names = ner.extract_names()
    chapter.add_names(names)


def analyze_names(
    analyzer: NameAnalyzer,
    metadata: BookDict,
    chapter: Chapter,
) -> None:
    analyzer.initialize_chapter(metadata, chapter)
    analyzer.build_role_script()
    analysis = analyzer.analyze_names()
    chapter.add_analysis(analysis)


def summarize_names(
    summarizer: NameSummarizer,
    binder: dict,
) -> dict:
    summarizer.build_role_script()
    return summarizer.summarize_names(binder)


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
) -> NameExtractor:
    ai = initialize_ai(
        provider=provider,
        family="openai",
        model_id=1,
        rate_limiter=rate_limiter,
    )
    return NameExtractor(ai)


def initializer_analyzer(
    provider: APIProvider, rate_limiter: RateLimitManager
) -> NameAnalyzer:
    model_id = 2
    ai = initialize_ai(
        provider=provider,
        family="openai",
        model_id=model_id,
        rate_limiter=rate_limiter,
    )
    model = ai.get_model(model_id)
    absolute_max_tokens = model.absolute_max_tokens
    return NameAnalyzer(
        ai,
        instruction_type="markdown",
        absolute_max_tokens=absolute_max_tokens,
    )


def initializer_summarizer(
    provider: APIProvider, rate_limiter: RateLimitManager
) -> NameSummarizer:
    ai = initialize_ai(
        provider=provider,
        family="openai",
        model_id=1,
        rate_limiter=rate_limiter,
    )
    return NameSummarizer(ai)


def build_binder(
    book: Book, ner: NameExtractor, analyzer: NameAnalyzer
) -> None:
    for chapter in book.chapters:
        perform_ner(ner, book.metadata, chapter)
        analyze_names(analyzer, book.metadata, chapter)


def summarize(book: Book, summarizer: NameSummarizer) -> None:
    binder = summarize_names(summarizer, book.binder)
    book.update_binder(binder)


def create_folder(folder: str, base_dir: str) -> str:
    created_path = os.path.join(base_dir, folder)
    os.makedirs(created_path, exist_ok=True)
    return created_path


def create_user(author: str) -> str:
    names = author.split(" ")
    return "_".join(names)


def create_user_folder(author: str, work_dir: str) -> str:
    user = create_user(author)
    return create_folder(user, work_dir)


def add_txt_filename(book_dict: BookDict, book_file: str) -> None:
    base, _ = os.path.splitext(book_file)
    txt_filename = f"{base}.txt"
    book_dict.txt_file = txt_filename


def convert(file_path: str, limited_metadata: dict) -> None:
    convert_file(file_path, limited_metadata)


def create_limited_metadata(book_dict: BookDict) -> dict:
    author = book_dict.author
    title = book_dict.title
    return {"title": title, "author": author}


def convert_book_file(book_dict: BookDict, work_dir: str) -> None:
    book_file = book_dict.book_file
    author = book_dict.author

    user_folder = create_user_folder(author, work_dir)
    file_path = os.path.join(user_folder, book_file)
    limited_metadata = create_limited_metadata(book_dict)
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

    build_binder(book, ner, analyzer)
    summarize(book, summarizer)

    if book_dict.user_folder is not None:
        make_pdf.create_pdf(book_dict.user_folder, book_dict.title)
