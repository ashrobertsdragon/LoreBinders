from __future__ import annotations

import os
import pathlib
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

from loguru import logger

from lorebinders._exceptions import BadEmailError
from lorebinders._managers import EmailManager

if TYPE_CHECKING:
    from lorebinders._type_annotations import Path


class SMTPHandler(EmailManager):
    def __init__(self) -> None:
        self.password: str = os.environ["MAIL_PASSWORD"]
        self.admin_email: str = os.environ["MAIL_USERNAME"]
        self.server: str = os.environ["MAIL_SERVER"]
        self.port: int = int(os.environ["MAIL_PORT"])
        self._email_server: smtplib.SMTP_SSL | None = None

    def _create_server(self) -> smtplib.SMTP_SSL:
        """
        Create the server object for the email.

        Returns:
            smtplib.SMTP_SSL: The server object for the email.
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
        if not self._email_server:
            self._email_server = self._create_server()
        return self._email_server

    def _get_email_body(self, body: str = "email_content.html") -> str:
        """
        Reads the contents of an html file and returns it as the email
        body text.

        Args:
            body (str, optional): The name of the html file to read. Defaults
                to 'email_content.html'.

        Returns:
            str: The contents of the html file.
        """
        html_path = pathlib.Path("lorebinders", "email_handlers", body)
        return html_path.read_text()

    def _get_attachment(self, attachment: tuple[str, str, str]) -> Path:
        """
        Unpack the tuple 'attachment' to retrieve the Path object for the path
        to the Binder to email.

        Args:
            attachment (tuple): The tuple containing the arguments to be
                unpacked.

        Returns:
            Path: The path to a PDF file using the variables from the
                unpacked tuple.
        """
        folder_name, book_name, binder = attachment
        return pathlib.Path(folder_name, f"{book_name}-{binder}.pdf")

    def send_mail(
        self,
        user_email: str,
        attachment: tuple[str, str, str] | None = None,
        error_msg: str | None = None,
    ) -> None:
        if message := self._build_email(user_email, attachment, error_msg):
            self.email_server.send_message(message)

    def _build_email(
        self,
        user_email: str,
        attachment: tuple[str, str, str] | None = None,
        error_msg: str | None = None,
    ) -> MIMEMultipart | None:
        """
        Send user the pdf of their story bible.

        Args:
            user_email (str): The email of the user to send the pdf to.
            attachment (tuple, optional): The tuple containing the path
                components to be unpacked. Defaults to None.
            error_msg (str, optional): The error message to send to the
                administrator. Defaults to None.
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
        """
        Create the MIMEBase object for the attachment.

        Args:
            file_path (Path): The path to the attachment.

        Returns:
            MIMEBase: The MIMEBase object for the attachment.
        """
        try:
            with open(file_path, "rb") as attachment_file:
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
        user_email,
        subject,
        email_body,
        file_path: Path | None = None,
    ):
        """
        Create the MIMEBase object for the email and send it.

        Args:
            user_email (str): The email of the user to send the email to.
            subject (str): The subject of the email.
            email_body (str): The body of the email.
            file_path (Path, optional): The path to the attachment. Defaults
                to None.
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
        """
        Send the administrator an error message.

        Args:
            error_msg (str) The error message to send to the administrator.
        """
        self.send_mail(self.admin_email, error_msg=error_msg)
