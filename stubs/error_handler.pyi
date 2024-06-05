from _managers import EmailManager as EmailManager
from _managers import ErrorManager
from _types import Book as Book
from _types import Logger as Logger

class ErrorHandler(ErrorManager):
    def __init__(cls, book: Book, email_manager: EmailManager) -> None: ...
    @classmethod
    def kill_app(cls, e: Exception) -> None: ...
