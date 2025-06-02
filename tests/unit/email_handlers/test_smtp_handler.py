import os
import smtplib
import pytest
from unittest.mock import call, patch, MagicMock

from lorebinders.email_handlers.smtp_handler import SMTPHandler
from lorebinders._exceptions import BadEmailError


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


def test_smtp_handler_init(smtp_handler):
    assert smtp_handler.password == "test_password"
    assert smtp_handler.admin_email == "test_username"
    assert smtp_handler.server == "smtp.example.com"
    assert smtp_handler.port == 587
    assert smtp_handler._email_server is None

# create_server tests
@patch("lorebinders.email_handlers.smtp_handler.smtplib.SMTP_SSL")
@patch("lorebinders.email_handlers.smtp_handler.logger")
def test_smtp_handler_create_server_success(mock_logger, MockSMTP_SSL, smtp_handler):

    mock_smtp = MockSMTP_SSL.return_value
    mock_smtp.login.return_value = None

    result = smtp_handler._create_server()

    MockSMTP_SSL.assert_called_once_with(host=smtp_handler.server, port=smtp_handler.port)
    mock_smtp.login.assert_called_once_with(smtp_handler.admin_email, smtp_handler.password)
    mock_logger.info.assert_called_once_with("Connected to email server")
    assert result == mock_smtp

@patch("lorebinders.email_handlers.smtp_handler.smtplib.SMTP_SSL")
@patch("lorebinders.email_handlers.smtp_handler.logger")
def test_smtp_handler_create_server_bad_email_error(mock_logger, MockSMTP_SSL, smtp_handler):

    mock_smtp = MockSMTP_SSL.return_value
    mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')

    with pytest.raises(BadEmailError):
        smtp_handler._create_server()

    MockSMTP_SSL.assert_called_once_with(host=smtp_handler.server, port=smtp_handler.port)
    mock_smtp.login.assert_called_once_with(smtp_handler.admin_email, smtp_handler.password)
    mock_logger.error.assert_called_once()

@patch.object(SMTPHandler, "_create_server")
def test_smtp_handler_email_server(mock_create_server, smtp_handler):

    smtp_handler._email_server = None
    mock_create_server.return_value = MagicMock()

    assert smtp_handler.email_server == mock_create_server.return_value
    mock_create_server.assert_called_once()
    assert smtp_handler._email_server is not None

# _get_* parts of email tests
@patch("pathlib.Path")
def test_smtp_handler_get_email_body(MockPath,smtp_handler):

    mock_path = MagicMock()
    MockPath.return_value = mock_path
    mock_path.return_value = "/lorebinders/email_handlers/email_content.html"
    mock_path.read_text.return_value="Test email body"

    result = smtp_handler._get_email_body()

    assert result == "Test email body"
    MockPath.assert_called_once_with("lorebinders", "email_handlers", "email_content.html")
    mock_path.read_text.assert_called_once()

@patch("pathlib.Path")
def test_smtp_handler_get_attachment(mock_path, smtp_handler):
    mock_path.return_value = "/test_folder/test_book-test_binder.pdf"
    attachment = ("test_folder", "test_book", "test_binder")
    expected_path = "/test_folder/test_book-test_binder.pdf"
    assert smtp_handler._get_attachment(attachment) == expected_path

# send_mail tests
@patch.object(SMTPHandler, "_build_email")
@patch.object(SMTPHandler, "email_server")
def test_smtp_handler_send_mail(mock_email_server, mock_build_email, smtp_handler):

    user_email = "Test user email"
    mock_build_email.return_value = "Test message"
    mock_send_message = MagicMock()
    mock_email_server.send_message.return_value = mock_send_message
    smtp_handler.send_mail(user_email)

    mock_build_email.assert_called_once_with(user_email, None, None)
    mock_email_server.send_message.assert_called_once_with("Test message")

# _build_email tests
@patch.object(SMTPHandler, "_get_email_body")
@patch.object(SMTPHandler, "_get_attachment")
@patch.object(SMTPHandler, "_create_email_object")
def test_smtp_handler_build_email_with_attachment(mock_create_email_object, mock_get_attachment, mock_get_email_body, smtp_handler):
    mock_get_attachment.return_value = "Test attachment"
    mock_get_email_body.return_value = "Test email body"
    user_email = "Test user email"
    mock_attachment_tuple = ("test_folder", "test_book", "test_binder")

    smtp_handler._build_email(user_email, attachment=mock_attachment_tuple)

    mock_get_attachment.assert_called_once_with(mock_attachment_tuple)
    mock_get_email_body.assert_called_once()
    mock_create_email_object.assert_called_once_with(user_email, "Your Binder is ready", "Test email body", file_path="Test attachment")

@patch.object(SMTPHandler, "_get_email_body")
@patch.object(SMTPHandler, "_get_attachment")
@patch.object(SMTPHandler, "_create_email_object")
def test_smtp_handler_build_email_without_attachment(mock_create_email_object, mock_get_attachment, mock_get_email_body, smtp_handler):

    mock_get_email_body.return_value = "Test email body"
    user_email = "Test user email"

    smtp_handler._build_email(user_email)

    mock_get_email_body.assert_called_once()
    mock_get_attachment.assert_not_called()
    mock_create_email_object.assert_called_once_with(user_email, "Your Binder is ready", "Test email body")

@patch.object(SMTPHandler, "_get_email_body")
@patch.object(SMTPHandler, "_get_attachment")
@patch.object(SMTPHandler, "_create_email_object")
@patch("lorebinders.email_handlers.smtp_handler.logger")
def test_smtp_handler_build_email_with_error_message(mock_logger, mock_create_email_object, mock_get_attachment, mock_get_email_body, smtp_handler):
    mock_get_email_body.reset_mock()
    user_email = "Test admin email"
    mock_error_msg = "Test error message"

    smtp_handler._build_email(user_email, error_msg=mock_error_msg)

    mock_get_email_body.assert_not_called()
    mock_get_attachment.assert_not_called()
    mock_logger.assert_not_called()
    mock_create_email_object.assert_called_once_with(user_email, "A critical error occurred", "Test error message")

@patch.object(SMTPHandler, "_get_email_body")
@patch.object(SMTPHandler, "_get_attachment")
@patch.object(SMTPHandler, "_create_email_object")
@patch("lorebinders.email_handlers.smtp_handler.logger")
def test_smtp_handler_build_email_raises_exception(mock_logger, mock_create_email_object, mock_get_attachment, mock_get_email_body, smtp_handler):
    user_email = "Test admin email"
    mock_attachment_tuple = ("test_folder", "test_book", "test_binder")
    mock_error_msg = "Test error message"

    smtp_handler._build_email(user_email, mock_attachment_tuple, mock_error_msg)
    mock_logger.exception.assert_called_once_with("Failed to send email. Reason: Cannot send error email with attachment")

    mock_get_email_body.assert_not_called()
    mock_get_attachment.assert_not_called()
    mock_create_email_object.assert_not_called()

# create_attachment tests
@patch("lorebinders.email_handlers.smtp_handler.MIMEBase")
@patch("lorebinders.email_handlers.smtp_handler.encoders.encode_base64")
def test_smtp_handler_create_attachment_valid_file_path(mock_encode_base64, mock_mime_base, smtp_handler):

    mock_file_path = MagicMock()
    mock_file_path.open.return_value.__enter__.return_value.read.return_value = b"file content"
    mock_mime_part = MagicMock()
    mock_mime_base.return_value = mock_mime_part
    mock_add_header = MagicMock()
    mock_mime_base.return_value.add_header = mock_add_header


    result = smtp_handler._create_attachment(mock_file_path)


    mock_mime_base.assert_called_once_with("application", "octet-stream")
    mock_mime_part.set_payload.assert_called_once_with(b"file content")
    mock_encode_base64.assert_called_once_with(mock_mime_part)
    mock_mime_part.add_header.assert_called_once_with(
        "Content-Disposition", f"attachment; filename= {mock_file_path}"
    )
    assert result == mock_mime_part

def test_smtp_handler_create_attachment_non_existent_file_path(smtp_handler):
    mock_file_path = MagicMock()
    mock_file_path.open.side_effect = FileNotFoundError("File not found")

    with pytest.raises(BadEmailError, match="Attachment file not found"):
        smtp_handler._create_attachment(mock_file_path)

# create_email_object tests
@patch("lorebinders.email_handlers.smtp_handler.MIMEMultipart")
@patch("lorebinders.email_handlers.smtp_handler.MIMEText")
def test_smtp_handler_create_email_object_no_attachment(mock_MIMEText, mock_MIMEMultipart, smtp_handler):
    user_email = "test@example.com"
    subject = "Test Subject"
    email_body = "This is a test email body."
    mock_msg = MagicMock()
    mock_MIMEMultipart.return_value = mock_msg
    mock_msg.__getitem__.side_effect = lambda key: {"To": user_email, "From": smtp_handler.admin_email, "Subject": subject}.get(key)

    result = smtp_handler._create_email_object(user_email, subject, email_body)

    mock_MIMEMultipart.assert_called_once()
    mock_MIMEText.assert_called_once_with(email_body, "html")
    assert result["To"] == user_email
    assert result["From"] == smtp_handler.admin_email
    assert result["Subject"] == subject
    mock_msg.attach.assert_called_once_with(mock_MIMEText.return_value)

@patch("lorebinders.email_handlers.smtp_handler.MIMEBase")
@patch("lorebinders.email_handlers.smtp_handler.MIMEMultipart")
@patch("lorebinders.email_handlers.smtp_handler.MIMEText")
@patch.object(SMTPHandler, "_create_attachment")
def test_smtp_handler_create_email_object_with_attachment(mock_create_attachment, mock_MIMEText, mock_MIMEMultipart, mock_MIMEBase, smtp_handler):
    user_email = "test@example.com"
    subject = "Test Subject"
    email_body = "Test Body"
    file_path = "test_file.txt"

    mock_msg = MagicMock()
    mock_MIMEMultipart.return_value = mock_msg
    mock_msg.__getitem__.side_effect = lambda key: {"To": user_email, "From": smtp_handler.admin_email, "Subject": subject}.get(key)

    attachment_part = mock_MIMEBase.return_value
    mock_create_attachment.return_value = attachment_part

    result = smtp_handler._create_email_object(user_email, subject, email_body, file_path)
    print(result.get_payload())
    assert result == mock_MIMEMultipart.return_value
    mock_msg.attach.assert_has_calls([call(attachment_part), call(mock_MIMEText.return_value)])
    mock_MIMEMultipart.assert_called_once()
    mock_MIMEText.assert_called_with(email_body, "html")

# error_email tests
@patch.object(SMTPHandler, "send_mail")
def test_smtp_handler_error_email_sends_email(mock_send_mail, smtp_handler):

    error_msg = "Test error message"
    smtp_handler.error_email(error_msg)
    mock_send_mail.assert_called_once_with(smtp_handler.admin_email, error_msg=error_msg)
