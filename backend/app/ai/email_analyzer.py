from app.ai.groq_service import run_llm


def analyze_emails(emails):

    formatted = ""

    for i, mail in enumerate(emails, 1):

        formatted += f"""
Email {i}
Sender: {mail['sender']}
Subject: {mail['subject']}
Snippet: {mail['snippet']}
"""

    prompt = f"""
You are an email assistant.

Analyze the following emails and answer the user's question.

Emails:
{formatted}

Provide a helpful short response.
"""

    response = run_llm.invoke(prompt)

    return response.content