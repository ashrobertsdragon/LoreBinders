import os
from unittest.mock import patch

import pytest

from lorebinders.email_handlers import SMTPHandler

@pytest.fixture
def smtp_handler():
    # set up
    with patch.dict(
        os.environ,
        {
            "MAIL_PASSWORD": "test_password",
            "MAIL_USERNAME": "test_username",
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": "587",
        },
    ):
        handler = SMTPHandler()

        yield handler

        # clean up
        del handler
def test_smtp_handler_create_email_object_no_attachment(smtp_handler):
    user_email = "test@example.com"
    subject = "Test Subject"
    email_body = "This is a test email body."

    result = smtp_handler._create_email_object(user_email, subject, email_body)

    assert result["To"] == user_email
    assert result["From"] == smtp_handler.admin_email
    assert result["Subject"] == subject
    assert len(result.get_payload()) == 1
    assert result.get_payload()[0].get_content_type() == "text/html"
    assert result.get_payload()[0].get_payload() == email_body
