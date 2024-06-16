from _typeshed import Incomplete

from _managers import EmailManager

class SMTPHandler(EmailManager):
    password: Incomplete
    admin_email: Incomplete
    server: Incomplete
    port: Incomplete
    def __init__(self) -> None: ...
    def send_mail(
        self,
        user_email: str,
        attachment: tuple[str, str, str] | None = None,
        error_msg: str | None = None,
    ) -> None: ...
    def error_email(self, error_msg: str) -> None: ...
