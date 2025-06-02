from __future__ import annotations

import pathlib
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

from decouple import config
from loguru import logger

from lorebinders._exceptions import BadEmailError
from lorebinders._managers import EmailManager

if TYPE_CHECKING:
    from lorebinders._type_annotations import Path


class SMTPHandler(EmailManager):
    """SMTP email handler for sending emails with attachments."""

    def __init__(self) -> None:
        """Initialize SMTP handler with configuration settings."""
        self.password: str = config("MAIL_PASSWORD")  # type: ignore
        self.admin_email: str = config("MAIL_USERNAME")  # type: ignore
        self.server: str = config("MAIL_SERVER")  # type: ignore
        self.port: int = config("MAIL_PORT", cast=int)
        self._email_server: smtplib.SMTP_SSL | None = None

    def _create_server(self) -> smtplib.SMTP_SSL:
        """Create the server object for the email.

        Returns:
            The server object for the email.

        Raises:
            BadEmailError: If authentication fails.
        """
        s = smtplib.SMTP_SSL(host=self.server, port=self.port)
        try:
            s.login(self.admin_email, self.password)
            logger.info("Connected to email server")
            return s
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Failed to login to email server: {e}")
            raise BadEmailError from e

    @property
    def email_server(self) -> smtplib.SMTP_SSL:
        """Get or create email server connection.

        Returns:
            The SMTP server connection.
        """
        if not self._email_server:
            self._email_server = self._create_server()
        return self._email_server

    def _get_email_body(self, body: str = "email_content.html") -> str:
        """Read the contents of an HTML file and return it as email body.

        Args:
            body: The name of the HTML file to read.

        Returns:
            The contents of the HTML file.
        """
        html_path = pathlib.Path("lorebinders", "email_handlers", body)
        return html_path.read_text()

    def _get_attachment(self, attachment: tuple[str, str, str]) -> Path:
        """Unpack attachment tuple to retrieve the PDF file path.

        Args:
            attachment: Tuple containing (folder_name, book_name, binder).

        Returns:
            Path to the PDF file.
        """
        folder_name, book_name, binder = attachment
        return pathlib.Path(folder_name, f"{book_name}-{binder}.pdf")

    def send_mail(
        self,
        user_email: str,
        attachment: tuple[str, str, str] | None = None,
        error_msg: str | None = None,
    ) -> None:
        """Send email to user with optional attachment or error message.

        Args:
            user_email: Recipient's email address.
            attachment: Optional tuple of (folder, book_name, binder).
            error_msg: Optional error message to include.
        """
        if message := self._build_email(user_email, attachment, error_msg):
            self.email_server.send_message(message)

    def _build_email(
        self,
        user_email: str,
        attachment: tuple[str, str, str] | None = None,
        error_msg: str | None = None,
    ) -> MIMEMultipart | None:
        """Build email message with content and optional attachment.

        Args:
            user_email: The recipient's email address.
            attachment: Optional tuple containing path components.
            error_msg: Optional error message for administrator.

        Returns:
            Built email message or None if failed.

        Raises:
            BadEmailError: If both error_msg and attachment provided.
        """
        email_body: str = error_msg or self._get_email_body()

        subject: str = (
            "A critical error occurred"
            if error_msg
            else "Your Binder is ready"
        )
        try:
            if error_msg and attachment:
                raise BadEmailError("Cannot send error email with attachment")
            if attachment:
                file_path: Path = self._get_attachment(attachment)
                return self._create_email_object(
                    user_email, subject, email_body, file_path=file_path
                )
            else:
                return self._create_email_object(
                    user_email, subject, email_body
                )
        except Exception as e:
            logger.exception(f"Failed to send email. Reason: {e}")
            return None

    def _create_attachment(self, file_path: Path) -> MIMEBase:
        """Create the MIMEBase object for the attachment.

        Args:
            file_path: The path to the attachment.

        Returns:
            The MIMEBase object for the attachment.

        Raises:
            BadEmailError: If attachment file not found.
        """
        try:
            with file_path.open("rb") as attachment_file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", f"attachment; filename= {file_path}"
                )
            return part
        except FileNotFoundError as e:
            raise BadEmailError("Attachment file not found") from e

    def _create_email_object(
        self,
        user_email: str,
        subject: str,
        email_body: str,
        file_path: Path | None = None,
    ) -> MIMEMultipart:
        """Create the MIMEMultipart object for the email.

        Args:
            user_email: The recipient's email address.
            subject: The subject of the email.
            email_body: The body of the email.
            file_path: Optional path to the attachment.

        Returns:
            The constructed email message.
        """
        msg = MIMEMultipart()
        msg["To"] = user_email
        msg["From"] = self.admin_email
        msg["Subject"] = subject
        if file_path:
            attachment_part = self._create_attachment(file_path)
            msg.attach(attachment_part)
        msg.attach(MIMEText(email_body, "html"))
        return msg

    def error_email(self, error_msg: str) -> None:
        """Send the administrator an error message.

        Args:
            error_msg: The error message to send to the administrator.
        """
        self.send_mail(self.admin_email, error_msg=error_msg)
