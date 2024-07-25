import os
import pytest
from unittest.mock import patch, MagicMock

from lorebinders.email_handlers.smtp_handler import SMTPHandler


@pytest.fixture
def smtp_handler():
    with patch.dict(
        os.environ,
        {
            "MAIL_PASSWORD": "test_password",
            "MAIL_USERNAME": "test_username",
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": "587",
        },
    ):
        return SMTPHandler()


def test_smtp_handler_init(smtp_handler):
    assert smtp_handler.password == "test_password"
    assert smtp_handler.admin_email == "test_username"
    assert smtp_handler.server == "smtp.example.com"
    assert smtp_handler.port == 587


@patch("pathlib.Path.read_text")
def test_get_email_body(mock_read_text, smtp_handler):
    mock_read_text.return_value = "Test email body"
    assert smtp_handler._get_email_body() == "Test email body"
    mock_read_text.assert_called_once_with()


def test_get_attachment(smtp_handler):
    attachment = ("test_folder", "test_book", "test_binder")
    expected_path = os.path.join("test_folder", "test_book-test_binder.pdf")
    assert smtp_handler._get_attachment(attachment) == expected_path


@patch("smtplib.SMTP_SSL")
@patch("smtplib.SMTP.send_message")
@patch("smtplib.SMTP.login")
def test_send_mail_with_attachment(
    mock_login, mock_send_message, mock_smtp_ssl, smtp_handler
):
    attachment = ("test_folder", "test_book", "test_binder")
    user_email = "test@example.com"
    mock_smtp_ssl.return_value = MagicMock()

    smtp_handler.send_mail(user_email, attachment=attachment)

    mock_smtp_ssl.assert_called_once_with(host="smtp.example.com", port=587)
    mock_login.assert_called_once_with("test_username", "test_password")
    mock_send_message.assert_called_once()


@patch("smtplib.SMTP_SSL")
@patch("smtplib.SMTP.send_message")
@patch("smtplib.SMTP.login")
def test_send_mail_without_attachment(
    mock_login, mock_send_message, mock_smtp_ssl, smtp_handler
):
    user_email = "test@example.com"
    mock_smtp_ssl.return_value = MagicMock()

    smtp_handler.send_mail(user_email)

    mock_smtp_ssl.assert_called_once_with(host="smtp.example.com", port=587)
    mock_login.assert_called_once_with("test_username", "test_password")
    mock_send_message.assert_called_once()


@patch("smtplib.SMTP_SSL")
@patch("smtplib.SMTP.send_message")
@patch("smtplib.SMTP.login")
def test_send_mail_with_error_message(
    mock_login, mock_send_message, mock_smtp_ssl, smtp_handler
):
    error_msg = "Test error message"
    user_email = "test@example.com"
    mock_smtp_ssl.return_value = MagicMock()

    smtp_handler.send_mail(user_email, error_msg=error_msg)

    mock_smtp_ssl.assert_called_once_with(host="smtp.example.com", port=587)
    mock_login.assert_called_once_with("test_username", "test_password")
    mock_send_message.assert_called_once()


@patch("smtplib.SMTP_SSL")
@patch("smtplib.SMTP.send_message")
@patch("smtplib.SMTP.login")
def test_error_email(
    mock_login, mock_send_message, mock_smtp_ssl, smtp_handler
):
    error_msg = "Test error message"
    mock_smtp_ssl.return_value = MagicMock()

    smtp_handler.error_email(error_msg)

    mock_smtp_ssl.assert_called_once_with(host="smtp.example.com", port=587)
    mock_login.assert_called_once_with("test_username", "test_password")
    mock_send_message.assert_called_once_with(
        "test_username",
        ["test_username"],
        f"A critical error occurred<br>{error_msg}",
    )
