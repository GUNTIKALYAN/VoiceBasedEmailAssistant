from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from app.utils.conversational_state import assistant_state
from app.gmail.send import send_email


# LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2
)

# Agent State 
class EmailState(TypedDict):

    recipient : str
    subject: str
    intent: str
    username: str
    recipient_name: str

    generated_email: str
    # user_decision: str
    # pin: str
    
# Node 1 -> Generate Email
def refine_subject(subject: str):

    prompt = f"""
Convert this into a professional email subject line.

Input:
{subject}

Rules:
- concise
- professional
- no extra words
- max 8 words
"""

    response = llm.invoke(prompt)

    return response.content.strip()


def generate_email(state: EmailState):

    prompt = f"""
Write a professional email BODY only.

Subject (for context, DO NOT include in output):
{state['subject']}

Recipient Name:
{state['recipient_name']}

User Intent:
{state['intent']}

STRICT RULES:
- DO NOT include "Subject:"
- DO NOT include "To:"
- Start with greeting using recipient name
- Example: Dear {state['recipient_name']},
- No placeholders like [Recipient Name]
- Keep it concise and professional

End with:
Best regards,
{state['username']}
"""

    response = llm.invoke(prompt)

    return {
        "generated_email": response.content
    }

# Node 2 -> Ask Confirmation
def confirm_email(state: EmailState):
    
    print("\nConfirming email with user...\n")

    return state

# Node 3 -> Pin Verification
def verify_pin(state: EmailState):

    correct_pin = "1234"

    if state["pin"] != correct_pin:
        raise ValueError("Invalid PIN")
    
    return state

# Node 4 -> Send Email
def send_email_node(state: EmailState):

    send_email(
        state["recipient"],
        state["subject"],
        state["generated_email"]
    )

    print("\nSending email to:", state["recipient"])

    return state

# Graph Definition

builder = StateGraph(EmailState)

builder.add_node("generate_email", generate_email)

builder.set_entry_point("generate_email")

builder.add_edge("generate_email", END)

email_agent = builder.compile()



# Public Function
def run_email_agent():

    state = {
        "recipient": assistant_state.recipient,
        "subject": assistant_state.subject,
        "intent": assistant_state.intent_line
    }

    result = email_agent.invoke(state)

    return result["generated_email"]


