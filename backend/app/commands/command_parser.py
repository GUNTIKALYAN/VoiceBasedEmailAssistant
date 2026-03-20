import re
import os
from datetime import datetime

from app.services.gmail_service import(
    fetch_recent_primary_emails,
    send_email,
    get_email_details
)
from app.services.whatsapp_service import fetch_recent_whatsapp_messages

from app.utils.conversational_state import assistant_state
from app.ai.email_understanding import understand_email_request, extract_email
from app.ai.groq_service import translate_and_summarize
from app.ai.email_agent import email_agent, refine_subject
from app.ai.email_analyzer import analyze_emails
from app.utils.voice_utils import normalize_email_full
from app.utils.voice_utils import normalize_confirmation

# NUMBER NORMALIZATION (All Languages + Roman)
NUMBER_MAP = {

    # English
    "one": 1, "first": 1,
    "two": 2, "second": 2,
    "three": 3, "third": 3,
    "four": 4, "fourth": 4,
    "five": 5, "fifth": 5,

    # Hindi native
    "एक": 1, "पहला": 1, "पहले": 1,
    "दो": 2, "दूसरा": 2,
    "तीन": 3, "तीसरा": 3,
    "चार": 4, "चौथा": 4,
    "पांच": 5, "पांचवा": 5,

    # Hindi roman
    "ek": 1, "pehla": 1,
    "do": 2, "dho": 2, "dusra": 2,
    "teen": 3, "teesra": 3,
    "char": 4,
    "paanch": 5,

    # Telugu native
    "ఒకటి": 1, "మొదటి": 1,
    "రెండు": 2, "రెండవ": 2,
    "మూడు": 3, "మూడవ": 3,
    "నాలుగు": 4,
    "ఐదు": 5,

    # Telugu roman
    "okati": 1,
    "rendu": 2,
    "moodu": 3,
    "nalugu": 4,
    "aidu": 5
}


INTRO_TEXT = {
    "en-IN": "Here are your latest emails.",
    "hi-IN": "ये आपके हाल के ईमेल हैं।",
    "te-IN": "ఇవి మీ తాజా మెయిల్స్."
}

ASK_NUMBER = {
    "en-IN": "Which email should I read?",
    "hi-IN": "कौन सा मेल पढ़ना है?",
    "te-IN": "ఏ మెయిల్ చదవాలి?"
}

FALLBACK_RESPONSE = {
    "en-IN": "Sorry, I did not understand.",
    "hi-IN": "माफ़ कीजिए, मैं समझ नहीं पाया।",
    "te-IN": "క్షమించండి, నేను అర్థం చేసుకోలేకపోయాను."
}


# SEND EMAIL AGENT
SEND_MAIL_TRIGGERS = [
    "send mail",
    "send email",
    "compose mail",
    "compose email",
    "write mail",
    "write email",
    "send a mail",
    "send an email"
]

SMART_EMAIL_QUERIES = [
    "urgent email",
    "urgent mails",
    "important email",
    "emails today",
    "any important mail",
    "do i have urgent mail",
    "which email needs reply"
]


ASK_RECIPIENT = {
    "en-IN": "Who should I send the email to?",
    "hi-IN": "ईमेल किसे भेजना है?",
    "te-IN": "ఈ మెయిల్ ఎవరికి పంపాలి?"
}

ASK_SUBJECT = {
    "en-IN": "What is the subject of the email?",
    "hi-IN": "ईमेल का विषय क्या है?",
    "te-IN": "మెయిల్ సబ్జెక్ట్ ఏమిటి?"
}

ASK_INTENT = {
    "en-IN": "Please tell me in one sentence what the email should say.",
    "hi-IN": "एक वाक्य में बताइए कि ईमेल में क्या लिखना है।",
    "te-IN": "మెయిల్‌లో ఏమి చెప్పాలో ఒక వాక్యంలో చెప్పండి."
}

PIN = os.getenv("VOICE_PIN","1234")

def extract_email_address(sender):

    import re

    match = re.search(r"<(.+?)>", sender)

    if match:
        return match.group(1)

    return sender


 
# HELPERS
def extract_number(command: str):
    """
    Extracts number from:
    - Digits
    - English words
    - Hindi words
    - Telugu words
    - Roman variations
    """
    command = command.lower()

    # Direct digit
    match = re.search(r"\d+", command)
    if match:
        return int(match.group())

    # Word match
    for word in command.split():
        if word in NUMBER_MAP:
            return NUMBER_MAP[word]

    return None


def save_summary_to_file(content, index, lang):
    """
    Saves AI translated + summarized email to text file.
    """

    folder = "summaries"

    if not os.path.exists(folder):
        os.makedirs(folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder}/email_{index}_{lang}_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved summary to {filename}")


def extract_speakable_email(content: str):

    lines = content.split("\n")
    clean_lines = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # skip garbage lines
        if any(x in line.lower() for x in ["subject:", "to:", "from:", "dear"]):
            continue

        clean_lines.append(line)

    return " ".join(clean_lines[:3])  # limit for speech

import os
from datetime import datetime

def save_email_to_file(to, subject, body):

    folder = "saved_emails"
    os.makedirs(folder, exist_ok=True)

    filename = f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(folder, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"To: {to}\n")
        f.write(f"Subject: {subject}\n\n")
        f.write(body)

    print(f" Email saved to {path}")

# MAIN PARSER
def parse_command(command: str):

    command = command.lower().strip()
    lang = assistant_state.session_language

    if any(x in command for x in [
        "whatsapp", "messages", "show whatsapp", "check whatsapp",

        # Hindi
        "व्हाट्सएप", "मैसेज", "संदेश",

        # Telugu
        "వాట్సాప్", "మెసేజ్", "సందేశాలు"
    ]):
        messages = fetch_recent_whatsapp_messages()

        if not messages:
            return {
                "en-IN": "No WhatsApp messages found.",
                "hi-IN": "कोई व्हाट्सएप संदेश नहीं मिला।",
                "te-IN": "వాట్సాప్ మెసేజ్లు లేవు."
            }.get(lang, "No WhatsApp messages found.")
        
        assistant_state.email_list = messages
        assistant_state.awaiting_email_selection = True

        lines = []

        header = {
            "en-IN": "Here are your recent WhatsApp messages.",
            "hi-IN": "ये आपके हाल के व्हाट्सएप संदेश हैं।",
            "te-IN": "ఇవి మీ తాజా వాట్సాప్ మెసేజ్లు."
        }.get(lang, "Here are your WhatsApp messages.")

        lines.append(header)
        lines.append("")

        for i, msg in enumerate(messages, 1):

            if lang == "hi-IN":
                line = f"{i} नंबर संदेश {msg['sender']} से।"
            elif lang == "te-IN":
                line = f"{i} నంబర్ మెసేజ్ {msg['sender']} నుండి."
            else:
                line = f"Message {i} from {msg['sender']}."

            lines.append(line)
        
        footer = {
            "en-IN": "Say the message number to open.",
            "hi-IN": "कृपया नंबर बोलें।",
            "te-IN": "నంబర్ చెప్పండి."
        }.get(lang, "Say the number.")

        lines.append("")
        lines.append(footer)

        return "\n".join(lines)
        
    #  WHATSAPP REPLY TRIGGER
    if "reply" in command:

        if not getattr(assistant_state, "current_whatsapp", None):
            return "Please open a WhatsApp message first."

        assistant_state.awaiting_whatsapp_reply = True

        return "What should I reply?"
    
    #  CAPTURE REPLY TEXT
    if getattr(assistant_state, "awaiting_whatsapp_reply", False):

        reply_text = command

        from app.services.whatsapp_service import send_whatsapp_message

        to_number = assistant_state.current_whatsapp["from"]

        success = send_whatsapp_message(to_number, reply_text)

        assistant_state.awaiting_whatsapp_reply = False

        if success:
            return "Reply sent successfully."
        else:
            return "Failed to send reply."



    if any(x in command for x in [
        # English
        "open inbox", "show inbox", "check inbox", "mails", "show emails", "show mail",
        # Hindi
        "मेल खोलो", "मेल दिखाओ", "इनबॉक्स खोलो",
        # Telugu
        "ఇన్‌బాక్స్", "ఇన్‌బాక్స్ చూపించు", "మెయిల్స్", "ఇన్బాక్స్"
    ]):

        assistant_state.awaiting_confirmation = False
        assistant_state.awaiting_pin = False
        assistant_state.send_mail_mode = False

        emails = fetch_recent_primary_emails(
            assistant_state.user_email
        )

        if not emails:
            return {
                "en-IN": "No emails found.",
                "hi-IN": "कोई ईमेल नहीं मिला।",
                "te-IN": "ఎలాంటి మెయిల్స్ లేవు."
            }.get(lang, "No emails found.")

        assistant_state.email_list = emails
        assistant_state.awaiting_email_selection = True

        print("\n---- EMAIL SENDERS ----")
        for i, mail in enumerate(emails, 1):
            print(f"{i}. {mail['sender']}")
        print("-----------------------\n")

        
        lines = []
        header = {
            "en-IN": "Here are your recent emails. ",
            "hi-IN": "यह आपके हाल के ईमेल हैं। ",
            "te-IN": "ఇవి మీ తాజా మెయిల్స్. "
        }.get(lang, "Here are your emails. ")

        lines.append(header)
        lines.append("")

        for i, mail in enumerate(emails, 1):

            if lang == "hi-IN":
                line = f"{i} नंबर मेल {mail['sender']} से। "
            elif lang == "te-IN":
                line = f"{i} నంబర్ మెయిల్ {mail['sender']} నుండి. "
            else:
                line = f"Email {i} from {mail['sender']}. "

            lines.append(line)

        footer = {
            "en-IN": "Say the email number to open.",
            "hi-IN": "कृपया नंबर बोलें।",
            "te-IN": "నంబర్ చెప్పండి."
        }.get(lang, "Say the number.")

        lines.append("")
        lines.append(footer)

        response = "\n".join(lines)
        
        return response


    #  NUMBER SELECTION (READ EMAIL)
    if assistant_state.awaiting_email_selection:

        if any(trigger in command for trigger in SEND_MAIL_TRIGGERS):
            assistant_state.awaiting_email_selection = False

            assistant_state.send_mail_mode = True
            assistant_state.awaiting_recipient = True

            return ASK_RECIPIENT.get(lang, ASK_RECIPIENT["en-IN"])

        index = extract_number(command)

        if index is None:
            return {
                "en-IN": "Please say a valid number.",
                "hi-IN": "कृपया सही नंबर बोलें।",
                "te-IN": "సరైన నంబర్ చెప్పండి."
            }.get(lang)

        if index < 1 or index > len(assistant_state.email_list):
            return {
                "en-IN": "Invalid number.",
                "hi-IN": "गलत नंबर।",
                "te-IN": "తప్పు నంబర్."
            }.get(lang)

        item = assistant_state.email_list[index-1]
        assistant_state.current_whatsapp = item

        if "snippet" in item:

            if lang == "hi-IN":
                return f"{item['sender']} ने कहा: {item['snippet']}"
            elif lang == "te-IN":
                return f"{item['sender']} చెప్పారు: {item['snippet']}"
            else:
                return f"{item['sender']} said: {item['snippet']}"

        email = get_email_details(
            assistant_state.user_email,
            item["id"]
        )

        assistant_state.current_email = email

        print("\n------ ORIGINAL EMAIL ------")
        print("From:", email["sender"])
        print("Subject:", email["subject"])
        print("----------------------------\n")

        ai_response = translate_and_summarize(email, lang)

        print("\n------ AI SUMMARY ------")
        print(ai_response)
        print("------------------------\n")

        save_summary_to_file(ai_response, index, lang)

        return ai_response


    # 2. START SEND EMAIL FLOW
    if "send email" in command or "write mail" in command:

        # assistant_state.reset()

        assistant_state.send_mail_mode = True
        assistant_state.awaiting_recipient = True

        return "Whom do you want to send the email to?"


    # RECIPIENT CAPTURE

    if assistant_state.send_mail_mode and assistant_state.awaiting_recipient:

        email = normalize_email_full(command)

        if "@" not in email or "." not in email:
            return "Please provide a valid email address."
        
        if len(email.split("@")[0]) < 3:
            return "Email username is too short. Please say again."
        
        assistant_state.recipient = email

        assistant_state.awaiting_recipient = False
        assistant_state.awaiting_recipient_confirmation = True

        return f"I heard {email}. Is that correct?"

    # RECIPIENT CONFIRMATION
    if assistant_state.send_mail_mode and assistant_state.awaiting_recipient_confirmation:
        
        decision = normalize_confirmation(command)

        if decision == "no":
            assistant_state.awaiting_recipient = True
            assistant_state.awaiting_recipient_confirmation = False
            return "Okay, please say the email again."

        elif decision == "yes":
            assistant_state.awaiting_subject = True
            assistant_state.awaiting_recipient_confirmation = False
            return "Tell me the subject."

        else:
            return "Please say yes or no."
        
    #  SUBJECT CAPTURE (LLM refine later)
    if assistant_state.send_mail_mode and assistant_state.awaiting_subject:

        refined_subject = refine_subject(command)
        assistant_state.subject = refined_subject
        assistant_state.awaiting_subject = False
        assistant_state.awaiting_intent = True

        return "What is the email about?"


    #  INTENT CAPTURE → GENERATE EMAIL
    from app.utils.voice_utils import extract_name_from_email

    if assistant_state.send_mail_mode and assistant_state.awaiting_intent:

        assistant_state.intent_line = command
        assistant_state.awaiting_intent = False


        recipient_name = extract_name_from_email(assistant_state.recipient)

        if not assistant_state.user_email:
            print("⚠️ user_email lost — recovering from session")
            return "Session lost. Please restart assistant."

        if not assistant_state.username:
            return "User info missing. Please login again."
        
        print("DEBUG → user_email:", assistant_state.user_email)
        
        # Generate email using agent
        result = email_agent.invoke({
            "recipient": assistant_state.recipient,
            "subject": assistant_state.subject,
            "intent": assistant_state.intent_line,
            "username": assistant_state.username,
            "recipient_name": recipient_name
        })

        assistant_state.generated_email = result["generated_email"]
        assistant_state.awaiting_confirmation = True
        assistant_state.send_mail_mode = True

        print("\n====== GENERATED EMAIL ======")
        print(f"To: {assistant_state.recipient}")
        print(f"Subject: {assistant_state.subject}")
        print("\nBody:\n")
        print(assistant_state.generated_email)
        print("================================\n")

        save_email_to_file(
            assistant_state.recipient,
            assistant_state.subject,
            assistant_state.generated_email
        )

        assistant_state.awaiting_confirmation = True
        spoken_text = extract_speakable_email(assistant_state.generated_email)

        #  Show email to user (important)
        return f"""
Here is your email:

-----------------------------------
To: {assistant_state.recipient}
Subject: {assistant_state.subject}

{assistant_state.generated_email}
-----------------------------------

I will read the summary:

{spoken_text}

Do you want to send it? Say 'yes send' or 'no change'.
"""


    #  CONFIRMATION STEP
    if assistant_state.awaiting_confirmation:
        cmd = command.lower()

        if "yes" in command or "send" in command:

            assistant_state.awaiting_confirmation = False
            assistant_state.awaiting_pin = True

            return "Please enter your 4 digit PIN."

        elif "rewrite" in command or "change" in command:

            assistant_state.awaiting_intent = True
            assistant_state.awaiting_confirmation = False

            return "Okay, tell me what changes you want."

        elif "cancel" in command or "stop" in command:

            assistant_state.reset()
            return "Email cancelled."


    #  PIN VERIFICATION → SEND EMAIL
    if assistant_state.awaiting_pin:

        if command == PIN:

            send_email(
                assistant_state.user_email,
                assistant_state.recipient,
                assistant_state.subject,
                assistant_state.generated_email
            )

            # assistant_state.reset()

            user_email = assistant_state.user_email
            username = assistant_state.username

            assistant_state.reset()

            assistant_state.user_email = user_email
            assistant_state.username = username

            return "Email sent successfully. What would you like to do next?"


        else:
            return "Incorrect PIN. Try again."


    # 7. REPLY FLOW
    REPLY_COMMANDS = ["reply", "reply to it", "reply to this"]

    if any(x in command for x in REPLY_COMMANDS):

        if not assistant_state.current_email:
            return "Please open an email first."

        sender = assistant_state.current_email["sender"]

        assistant_state.send_mail_mode = True
        assistant_state.recipient = extract_email_address(sender)

        assistant_state.subject = "Re: " + assistant_state.current_email["subject"]

        assistant_state.awaiting_intent = True

        return "What should I reply?"


    # 8. DEFAULT
    return FALLBACK_RESPONSE.get(lang, FALLBACK_RESPONSE["en-IN"])
