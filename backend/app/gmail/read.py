from app.gmail.auth import get_gmail_service

LAST_FETCHED_EMAILS = []


def fetch_recent_primary_emails(max_results=5):

    service = get_gmail_service()

    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        q="category:primary",
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        return []

    global LAST_FETCHED_EMAILS
    LAST_FETCHED_EMAILS = []

    for msg_data in messages:

        msg = service.users().messages().get(
            userId='me',
            id=msg_data['id'],
            format="full"
        ).execute()

        headers = msg['payload']['headers']

        subject = "No Subject"
        sender = "Unknown Sender"

        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            if header['name'] == 'From':
                sender = header['value']

        snippet = msg.get("snippet", "")

        LAST_FETCHED_EMAILS.append({
            "sender": sender,
            "subject": subject,
            "snippet": snippet
        })

    return LAST_FETCHED_EMAILS


def read_email_details_by_index(index):

    if not LAST_FETCHED_EMAILS:
        return None

    if index < 1 or index > len(LAST_FETCHED_EMAILS):
        return None

    return LAST_FETCHED_EMAILS[index - 1]

def fetch_primary_emails_for_ui(max_results=10):

    service = get_gmail_service()

    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        q="category:primary",
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    emails = []

    for msg_data in messages:

        msg = service.users().messages().get(
            userId='me',
            id=msg_data['id'],
            format="full"
        ).execute()

        headers = msg['payload']['headers']

        subject = "No Subject"
        sender = "Unknown Sender"

        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            if header['name'] == 'From':
                sender = header['value']

        snippet = msg.get("snippet", "")

        emails.append({
            "sender": sender,
            "subject": subject,
            "snippet": snippet
        })

    return emails