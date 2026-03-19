import re
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"


def extract_email(text: str):

    match = re.search(EMAIL_REGEX, text)

    if match:
        return match.group()

    return None


def understand_email_request(command: str):

    prompt = f"""
Extract the following from the user request.

User request:
{command}

Return JSON with keys:
recipient
subject
intent

Rules:
- If missing fields, return null.
"""

    response = llm.invoke(prompt)

    try:
        import json
        return json.loads(response.content)
    except:
        return {
            "recipient": None,
            "subject": None,
            "intent": None
        }