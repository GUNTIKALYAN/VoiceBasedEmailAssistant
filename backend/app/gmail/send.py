import base64
from email.mime.text import MIMEText
from app.gmail.auth import get_gmail_service

def send_email(recipient: str, subject: str, body: str):

    service = get_gmail_service()

    message = MIMEText(body)
    message["to"] = recipient
    message["subject"] = subject

    raw_message = base64.urlsafe_b64decode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={"raw" : raw_message}
    ).execute()

    print("Email sent successfully")