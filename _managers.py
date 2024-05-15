from abc import ABC, abstractmethod
from typing import Optional, Tuple

class EmailManager(ABC):
    @abstractmethod
    def send_mail(self, user_email: str, attachment: Optional[Tuple[str, str, str]] = None, error_msg: Optional[bool] = False, ) -> None:
        raise NotImplementedError("subclass must implement send_mail")
    
    @abstractmethod
    def error_email(self, error_msg: str) -> None:
        raise NotImplementedError("subclass must implement error_email")

class ErrorManager(ABC):
    @classmethod @abstractmethod
    def kill_app(cls, e: Exception) -> None:
        raise NotImplementedError("subclass must implement kil_app")

class FileManager(ABC):
    @abstractmethod
    def read_text_file(self, file_path: str) -> str:
        raise NotImplementedError("subclass must implement read_text_file")
    @abstractmethod
    def read_json_file(self, file_path: str) -> str:
        raise NotImplementedError("subclass must implement read_json_file")
    @abstractmethod
    def write_to_file(self, content: any, file_path: str) -> None:
        raise NotImplementedError("subclass must implement write_to_file")
    @abstractmethod
    def separate_into_chapters(self, text: str) -> list:
        raise NotImplementedError("subclass must implement seperate_into_chapters")
    @abstractmethod
    def write_json_file(self, content: any, file_path: str) -> None:
        raise NotImplementedError("subclass must implement write_json_file")
    @abstractmethod
    def append_json_file(self, content: any, file_path: str) -> None:
        raise NotImplementedError("subclass must implement append_json)file")
