import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

if not os.path.exists(".replit"):
  from dotenv import load_dotenv
  load_dotenv()

def get_email_body() -> str:
  """
  Reads the contents of an html file and returns it as the email body text.
  """
  
  with open ("email_content.html", "r") as f:
    email_body = f.read()


  return email_body
  
def send_mail(folder_name: str, book_name: str, user_email: str) -> None:
  """
  Send user the pdf of their story bible.

  Arguments:
    folder_name: Name of the folder containing the story bible.
    book_name: Name of the book.
    user_email: Email address of the user.
  """

  password = os.environ['mail_password']
  username = os.environ['mail_username']

  server = "prosepal.io"
  port = 465

  file_path = os.path.join(folder_name, f"{book_name}.pdf")

  email_body = get_email_body()

  try:
    s = smtplib.SMTP_SSL(host = server, port = port)
    s.login(username, password)

    msg = MIMEMultipart()
    msg["To"] =  user_email
    msg["From"] = username
    msg["Subject"] = "Your PlotBinder is ready"
    with open(file_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {file_path}")
    msg.attach(part)
    msg.attach(MIMEText(email_body, "html"))
    s.send_message(msg)
    print("email sent")
  except Exception as e:
    print(f"Failed to send email. Reason: {e}")
  return

def email_error(error: str) -> None:
  """
  Send user the pdf of their story bible.

  Arguments:
    folder_name: Name of the folder containing the story bible.
    book_name: Name of the book.
    user_email: Email address of the user.
  """

  error_email = os.environ['error_email']
  password = os.environ['mailPassword']
  username = os.environ['mailUsername']
  server = "prosepal.io"
  port = 465

  email_body = error

  try:
    s = smtplib.SMTP_SSL(host = server, port = port)
    s.login(username, password)

    msg = MIMEMultipart()
    msg["To"] =  error_email
    msg["From"] = username
    msg["Subject"] = "A critical error occured"
    msg.attach(MIMEText(email_body, "html"))
    s.send_message(msg)
    print("email sent")
  except Exception as e:
    print(f"Failed to send email. Reason: {e}")
  return