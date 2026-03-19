# # from google.oauth2.credentials import Credentials
# # from googleapiclient.discovery import build
# # from google.auth.transport.requests import Request

# # from app.db import user_auth_collection


# # def get_gmail_service(user_email: str):

# #     user = user_auth_collection.find_one({"email": user_email})

# #     if not user:
# #         raise Exception("User not found")

# #     token = user.get("google_token")

# #     if not token:
# #         raise Exception("User has not connected Gmail")

# #     creds = Credentials(
# #         token=token["access_token"],
# #         refresh_token=token.get("refresh_token"),
# #         token_uri="https://oauth2.googleapis.com/token",
# #         client_id=None,
# #         client_secret=None
# #     )

# #     # Refresh token automatically
# #     if creds.expired and creds.refresh_token:
# #         creds.refresh(Request())

# #         # update new token in database
# #         user_auth_collection.update_one(
# #             {"email": user_email},
# #             {
# #                 "$set": {
# #                     "google_token.access_token": creds.token
# #                 }
# #             }
# #         )

# #     service = build("gmail", "v1", credentials=creds)

# #     return service


# # def read_latest_emails(user_email: str, max_results=5):

# #     service = get_gmail_service(user_email)

# #     results = service.users().messages().list(
# #         userId="me",
# #         maxResults=max_results
# #     ).execute()

# #     messages = results.get("messages", [])

# #     email_list = []

# #     for msg in messages:

# #         message = service.users().messages().get(
# #             userId="me",
# #             id=msg["id"]
# #         ).execute()

# #         headers = message["payload"]["headers"]

# #         subject = ""
# #         sender = ""

# #         for header in headers:
# #             if header["name"] == "Subject":
# #                 subject = header["value"]

# #             if header["name"] == "From":
# #                 sender = header["value"]

# #         email_list.append({
# #             "from": sender,
# #             "subject": subject
# #         })

# #     return email_list



# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build
# from google.auth.transport.requests import Request

# from app.db import user_auth_collection
# import os


# def get_gmail_service(user_email: str):

#     user = user_auth_collection.find_one({"email": user_email})

#     if not user:
#         raise Exception("User not found")

#     token = user.get("google_token")

#     if not token:
#         raise Exception("User has not connected Gmail")

#     creds = Credentials(
#         token=token["access_token"],
#         refresh_token=token.get("refresh_token"),
#         token_uri="https://oauth2.googleapis.com/token",
#         client_id=os.getenv("GOOGLE_CLIENT_ID"),
#         client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
#     )

#     # refresh expired token
#     if creds.expired and creds.refresh_token:
#         creds.refresh(Request())

#         user_auth_collection.update_one(
#             {"email": user_email},
#             {
#                 "$set": {
#                     "google_token.access_token": creds.token
#                 }
#             }
#         )

#     service = build("gmail", "v1", credentials=creds)

#     return service

# def fetch_recent_primary_emails(user_email, max_results=5):

#     service = get_gmail_service(user_email)

#     results = service.users().messages().list(
#         userId="me",
#         labelIds=["INBOX"],
#         q="category:primary",
#         maxResults=max_results
#     ).execute()

#     messages = results.get("messages", [])

#     email_list = []

#     for msg in messages:

#         message = service.users().messages().get(
#             userId="me",
#             id=msg["id"],
#             format="full"
#         ).execute()

#         headers = message["payload"]["headers"]

#         subject = "No Subject"
#         sender = "Unknown Sender"

#         for header in headers:

#             if header["name"] == "Subject":
#                 subject = header["value"]

#             if header["name"] == "From":
#                 sender = header["value"]

#         snippet = message.get("snippet", "")

#         email_list.append({
#             "sender": sender,
#             "subject": subject,
#             "snippet": snippet
#         })

#     return email_list


# import base64
# from email.mime.text import MIMEText


# def send_email(user_email, recipient, subject, body):

#     service = get_gmail_service(user_email)

#     message = MIMEText(body)

#     message["to"] = recipient
#     message["subject"] = subject

#     raw_message = base64.urlsafe_b64encode(
#         message.as_bytes()
#     ).decode()

#     service.users().messages().send(
#         userId="me",
#         body={"raw": raw_message}
#     ).execute()

#     return "Email sent successfully"


import os
import base64
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from app.db import user_auth_collection

def clean_html(html):

    soup = BeautifulSoup(html, "html.parser")

    # remove scripts and styles
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    return " ".join(text.split())

def get_gmail_service(user_email: str):

    user = user_auth_collection.find_one({"email": user_email})

    if not user:
        raise Exception("User not found")

    token = user.get("google_token")

    if not token:
        raise Exception("User Gmail not connected")

    creds = Credentials(
        token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )

    # refresh expired token
    if creds.expired and creds.refresh_token:

        creds.refresh(Request())

        user_auth_collection.update_one(
            {"email": user_email},
            {
                "$set": {
                    "google_token.access_token": creds.token
                }
            }
        )

    service = build("gmail", "v1", credentials=creds)

    return service


def fetch_recent_primary_emails(user_email: str, max_results=5):

    service = get_gmail_service(user_email)

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="category:primary -category:promotions",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])

    email_list = []

    for msg in messages:

        message = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["Subject", "From"]
        ).execute()

        headers = message["payload"]["headers"]

        subject = "No Subject"
        sender = "Unknown Sender"

        for header in headers:

            if header["name"] == "Subject":
                subject = header["value"]

            if header["name"] == "From":
                sender = header["value"]

        snippet = message.get("snippet", "")

        email_list.append({
            "id" : msg["id"],
            "sender": sender,
            "subject": subject,
            "snippet": snippet
        })

    return email_list

def extract_email_body(payload):

    if "parts" in payload:

        for part in payload["parts"]:

            mime_type = part.get("mimeType")

            if mime_type == "text/plain":

                data = part["body"].get("data")

                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8")

            if mime_type == "text/html":

                data = part["body"].get("data")

                if data:
                    html = base64.urlsafe_b64decode(data).decode("utf-8")
                    return clean_html(html)

            # recursive for nested parts
            if "parts" in part:
                return extract_email_body(part)

    else:

        data = payload["body"].get("data")

        if data:
            html = base64.urlsafe_b64decode(data).decode("utf-8")
            return clean_html(html)

    return ""

def get_email_details(user_email, message_id):

    service = get_gmail_service(user_email)

    msg = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    headers = msg["payload"]["headers"]

    subject = "No Subject"
    sender = "Unknown Sender"

    for header in headers:

        if header["name"] == "Subject":
            subject = header["value"]

        if header["name"] == "From":
            sender = header["value"]

    body = extract_email_body(msg["payload"])

    return {
        "sender": sender,
        "subject": subject,
        "body": body
    }


def send_email(user_email: str, recipient: str, subject: str, body: str):

    service = get_gmail_service(user_email)

    message = MIMEText(body)

    message["to"] = recipient
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw_message}
    ).execute()

    return "Email sent successfully"