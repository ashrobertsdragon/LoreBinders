import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple

from _managers import EmailManager


class EmailHandler(EmailManager):
    def __init__(self) -> None:
        self.password: str = os.environ["MAIL_PASSWORD"]
        self.admin_email: str = os.environ["MAIL_USERNAME"]
        self.server: str = os.environ["MAIL_SERVER"]
        self.port: int = int(os.environ["MAIL_PORT"])

    def _get_email_body(self) -> str:
        """
        Reads the contents of an html file and returns it as the email
        body text.
        """
        html_path: str = os.path.join("ProsePal", "email_content.html")
        with open(html_path) as f:
            email_body = f.read()

        return email_body

    def _get_attachment(self, attachment: Tuple[str, str, str]) -> str:
        """
        Unpack the tuple 'attachment' to retrieve the path to the Binder to
        email.

        Args:
            attachment (tuple): The tuple containing the arguments to be
                unpacked.

        Returns:
            A string of the path to a PDF file using the variables from the
                unpacked tuple.
        """
        folder_name, book_name, binder = attachment
        return os.path.join(folder_name, f"{book_name}-{binder}.pdf")

    def send_mail(
        self,
        user_email: str,
        attachment: Optional[Tuple[str, str, str]] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        """
        Send user the pdf of their story bible.

        Arguments:
            folder_name: Name of the folder containing the story bible.
            book_name: Name of the book.
            user_email: Email address of the user.
        """
        if attachment:
            file_path: str = self._get_attachment(attachment)

        email_body = error_msg if error_msg else self._get_email_body()

        subject = (
            "A critical error occured" if error_msg else "Your Binder is ready"
        )
        try:
            s = smtplib.SMTP_SSL(host=self.server, port=self.port)
            s.login(self.admin_email, self.password)

            msg = MIMEMultipart()
            msg["To"] = user_email
            msg["From"] = self.admin_email
            msg["Subject"] = subject
            with open(file_path, "rb") as attachment_file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_file.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename= {file_path}"
            )
            msg.attach(part)
            msg.attach(MIMEText(email_body, "html"))
            s.send_message(msg)
            print("email sent")
        except Exception as e:
            print(f"Failed to send email. Reason: {e}")
        return

    def error_email(self, error_msg: str) -> None:
        """
        Send the administrator an error message.

        Args:
            error_msg (str) The error message to send to the administrator.
        """
        self.send_mail(self.admin_email, error_msg=error_msg)
