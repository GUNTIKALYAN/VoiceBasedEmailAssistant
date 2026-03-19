import re
import os
from datetime import datetime

from app.services.gmail_service import(
    fetch_recent_primary_emails,
    send_email,
    get_email_details
)

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
        # English
        "open inbox", "show inbox", "check inbox", "mails", "show emails", "show mail",
        # Hindi
        "मेल खोलो", "मेल दिखाओ", "इनबॉक्स खोलो",
        # Telugu
        "ఇన్‌బాక్స్", "ఇన్‌బాక్స్ చూపించు", "మెయిల్స్"
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


    # ─────────────────────────────────────────
    # 📧 NUMBER SELECTION (READ EMAIL)
    # ─────────────────────────────────────────
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

        email_meta = assistant_state.email_list[index - 1]

        email = get_email_details(
            assistant_state.user_email,
            email_meta["id"]
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


    # ─────────────────────────────────────────
    # 2. START SEND EMAIL FLOW
    # ─────────────────────────────────────────
    if "send email" in command or "write mail" in command:

        # assistant_state.reset()

        assistant_state.send_mail_mode = True
        assistant_state.awaiting_recipient = True

        return "Whom do you want to send the email to?"


    # ─────────────────────────────────────────
    # 2. RECIPIENT CAPTURE
    # ─────────────────────────────────────────

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

    # ─────────────────────────────────────────
    # RECIPIENT CONFIRMATION
    # ─────────────────────────────────────────
    if assistant_state.send_mail_mode and assistant_state.awaiting_recipient_confirmation:
        # cmd = command.lower().strip()

        # YES_WORDS = ["yes", "yeah", "correct", "ok", "okay"]
        # NO_WORDS = ["no", "not", "wrong", "incorrect"]

        # if any(word in cmd for word in NO_WORDS):

        #     assistant_state.awaiting_recipient_confirmation = False
        #     assistant_state.awaiting_recipient = True

        #     return "Okay, please say the email again."

        # # THEN check YES
        # elif any(word in cmd for word in YES_WORDS):

        #     assistant_state.awaiting_recipient_confirmation = False
        #     assistant_state.awaiting_subject = True

        #     return "Tell me the subject."

        # else:
        #     return "Please say yes or no clearly."
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
        
    # ─────────────────────────────────────────
    # 3. SUBJECT CAPTURE (LLM refine later)
    # ─────────────────────────────────────────
    if assistant_state.send_mail_mode and assistant_state.awaiting_subject:

        refined_subject = refine_subject(command)
        assistant_state.subject = refined_subject
        assistant_state.awaiting_subject = False
        assistant_state.awaiting_intent = True

        return "What is the email about?"


    # ─────────────────────────────────────────
    # 4. INTENT CAPTURE → GENERATE EMAIL
    # ─────────────────────────────────────────
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

        # 👇 Show email to user (important)
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


    # ─────────────────────────────────────────
    # 5. CONFIRMATION STEP
    # ─────────────────────────────────────────
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


    # ─────────────────────────────────────────
    # 6. PIN VERIFICATION → SEND EMAIL
    # ─────────────────────────────────────────
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


    # ─────────────────────────────────────────
    # 7. REPLY FLOW
    # ─────────────────────────────────────────
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


    # ─────────────────────────────────────────
    # 8. DEFAULT
    # ─────────────────────────────────────────
    return FALLBACK_RESPONSE.get(lang, FALLBACK_RESPONSE["en-IN"])



# def parse_command(command: str):


#     command = command.lower().strip()
#     lang = assistant_state.session_language


#     # SMART EMAIL REQUEST
#     if "send email" in command or "write mail" in command:

#         parsed = understand_email_request(command)

#         if parsed["recipient"]:
#             assistant_state.recipient = parsed["recipient"]

#         if parsed["subject"]:
#             assistant_state.subject = parsed["subject"]

#         if parsed["intent"]:
#             assistant_state.intent_line = parsed["intent"]

#         if assistant_state.recipient and assistant_state.subject and assistant_state.intent_line:

#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject": assistant_state.subject,
#                 "intent": assistant_state.intent_line
#             })

#             assistant_state.generated_email = result["generated_email"]
#             assistant_state.awaiting_confirmation = True

#             return "I generated an email based on your request. Do you want to send it?"

#     if any(x in command for x in REPLY_COMMANDS):

#         if not assistant_state.current_email:
#             return "Please open an email first."
        
#         sender = assistant_state.current_email["sender"]

#         assistant_state.recipient = extract_email_address(sender)

#         assistant_state.awaiting_intent = True

#         return "What should I reply?"

#     # SEND EMAIL ACTIVATION
#     if any(trigger in command for trigger in SEND_MAIL_TRIGGERS):

#         assistant_state.send_mail_mode = True
#         assistant_state.awaiting_recipient = True

#         return ASK_RECIPIENT.get(lang, ASK_RECIPIENT["en-IN"])

#     # RECIPIENT CAPTURE
#     if assistant_state.send_mail_mode and assistant_state.awaiting_recipient:

#         assistant_state.recipient = command
#         assistant_state.awaiting_recipient = False
#         assistant_state.awaiting_subject = True

#         return ASK_SUBJECT.get(lang, ASK_SUBJECT["en-IN"])

#     # SMART EMAIL ANALYSIS
#     if any(q in command for q in SMART_EMAIL_QUERIES):

#         emails = fetch_recent_primary_emails(
#             assistant_state.user_email
#         )

#         if not emails:
#             return "You have no recent emails."

#         analysis = analyze_emails(emails)

#         return analysis
    
#     # SUBJECT CAPTURE
#     if assistant_state.send_mail_mode and assistant_state.awaiting_subject:

#         assistant_state.subject = command
#         assistant_state.awaiting_subject = False
#         assistant_state.awaiting_intent = True

#         return ASK_INTENT.get(lang, ASK_INTENT["en-IN"])
    
#     # EMAIL INTENT CAPTURE
#     if assistant_state.send_mail_mode and assistant_state.awaiting_intent:

#         assistant_state.intent_line = command
#         assistant_state.awaiting_intent = False

#         if assistant_state.current_email:

#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject": "Re:" + assistant_state.current_email["subject"],
#                 "intent": assistant_state.intent_line,
#                 "context": assistant_state.current_email["body"]
#             })
#         else:

#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject": assistant_state.subject,
#                 "intent": assistant_state.intent_line
#             })

#         assistant_state.generated_email = result["generated_email"]

#         print("\nEMAIL TEMPLATE\n")
#         print(assistant_state.generated_email)

#         assistant_state.awaiting_confirmation = True

#         return "I have created the email. Do you want to send it?"
    
#     # CONFIRMATION
#     if assistant_state.awaiting_confirmation:
#         if "send" in command:

#             assistant_state.awaiting_confirmation = False
#             assistant_state.awaiting_pin = True

#             return "Please provide your four digit security pin."

#         if "rewrite" in command or "change" in command:

#             assistant_state.awaiting_intent = True
#             assistant_state.awaiting_confirmation = False

#             return "Please provide your four digit security pin."
        
#         if "cancel" in command or "stop" in command:

#             assistant_state.reset()

#             return "Email cancelled."
        
#     # PIN VERIFICATION
#     if assistant_state.awaiting_pin:

#         if command == "1234":

#             send_email(
#                 assistant_state.user_email,
#                 assistant_state.recipient,
#                 assistant_state.subject,
#                 assistant_state.generated_email
#             )

#             assistant_state.reset()

#             return "Email sent successfully."

#         else:
#             return "Incorrect pin. Please try again."

    


#     # NUMBER SELECTION MODE
#     if assistant_state.awaiting_email_selection:

#         index = extract_number(command)

#         if index is None:
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         if index < 1 or index > len(assistant_state.email_list):
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         email_meta = assistant_state.email_list[index - 1]

#         from app.services.gmail_service import get_email_details

#         email = get_email_details(
#             assistant_state.user_email,
#             email_meta["id"]
#         )

#         if not email:
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])
        
#         assistant_state.current_email = email
#         assistant_state.current_email_index = index
#         assistant_state.awaiting_email_selection = True

#         # Print full original email in terminal
#         print("\n------ ORIGINAL EMAIL ------")
#         print("From:", email["sender"])
#         print("Subject:", email["subject"])
#         print("----------------------------\n")

#         # AI Translation + Summarization
#         ai_response = translate_and_summarize(email, lang)

#         # Print AI result
#         print("\n------ AI TRANSLATED + SUMMARY ------")
#         print(ai_response)
#         print("-------------------------------------\n")

#         # Save to file
#         save_summary_to_file(ai_response, index, lang)

#         return ai_response + " " + ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])


#     # OPEN INBOX COMMAND
#     if any(x in command for x in [
#         "मेल खोलो", "मेल दिखाओ", "इनबॉक्स खोलो", "मेल",
#         "open inbox", "show inbox", "check inbox", "mails", "show emails", "show email", "show mail",
#         "ఇన్‌బాక్స్", "ఇన్‌బాక్స్ చూపించు", "మెయిల్స్", "open mail","చూపించు", "మెయిల్స్ చూపించు"
#     ]):

#         emails = fetch_recent_primary_emails(
#             assistant_state.user_email
#         )

#         if not emails:
#             return {
#                 "en-IN": "No emails found.",
#                 "hi-IN": "कोई ईमेल नहीं मिला।",
#                 "te-IN": "ఎలాంటి మెయిల్స్ లేవు."
#             }.get(lang, "No emails found.")

#         assistant_state.email_list = emails
#         assistant_state.awaiting_email_selection = True

#         # Print only senders in terminal
#         print("\n---- EMAIL SENDERS ----")
#         for i, mail in enumerate(emails, 1):
#             print(f"{i}. {mail['sender']}")
#         print("-----------------------\n")

#         response = INTRO_TEXT.get(lang, INTRO_TEXT["en-IN"]) + " "

#         for i, mail in enumerate(emails, 1):

#             if lang == "hi-IN":
#                 response += f"{i} नंबर मेल {mail['sender']} से। "
#             elif lang == "te-IN":
#                 response += f"{i} నంబర్ మెయిల్ {mail['sender']} నుండి. "
#             else:
#                 response += f"Email {i} from {mail['sender']}. "

#         response += ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         return response


    
#     # DEFAULT FALLBACK
#     return FALLBACK_RESPONSE.get(lang, FALLBACK_RESPONSE["en-IN"])





# import re
# import os
# from datetime import datetime

# from app.services.gmail_service import (
#     fetch_recent_primary_emails,
#     send_email
# )

# from app.utils.conversational_state import assistant_state
# from app.ai.email_understanding import understand_email_request
# from app.ai.groq_service import translate_and_summarize
# from app.ai.email_agent import email_agent
# from app.ai.email_analyzer import analyze_emails


# # ---------------------------------------------------------------------------
# # NUMBER NORMALIZATION  (digits + English + Hindi native + Hindi roman +
# #                        Telugu native + Telugu roman)
# # ---------------------------------------------------------------------------

# NUMBER_MAP = {

#     # English
#     "one": 1, "first": 1,
#     "two": 2, "second": 2,
#     "three": 3, "third": 3,
#     "four": 4, "fourth": 4,
#     "five": 5, "fifth": 5,

#     # Hindi native
#     "एक": 1, "पहला": 1, "पहले": 1,
#     "दो": 2, "दूसरा": 2,
#     "तीन": 3, "तीसरा": 3,
#     "चार": 4, "चौथा": 4,
#     "पांच": 5, "पांचवा": 5,

#     # Hindi roman
#     "ek": 1, "pehla": 1,
#     "do": 2, "dho": 2, "dusra": 2,
#     "teen": 3, "teesra": 3,
#     "char": 4,
#     "paanch": 5,

#     # Telugu native
#     "ఒకటి": 1, "మొదటి": 1,
#     "రెండు": 2, "రెండవ": 2,
#     "మూడు": 3, "మూడవ": 3,
#     "నాలుగు": 4,
#     "ఐదు": 5,

#     # Telugu roman
#     "okati": 1, "modati": 1,
#     "rendu": 2, "rendava": 2,
#     "moodu": 3, "moodava": 3,
#     "nalugu": 4,
#     "aidu": 5,
# }


# # ---------------------------------------------------------------------------
# # STATIC RESPONSE STRINGS
# # ---------------------------------------------------------------------------

# INTRO_TEXT = {
#     "en-IN": "Here are your latest emails.",
#     "hi-IN": "ये आपके हाल के ईमेल हैं।",
#     "te-IN": "ఇవి మీ తాజా మెయిల్స్.",
# }

# ASK_NUMBER = {
#     "en-IN": "Which email should I read? Please say a number.",
#     "hi-IN": "कौन सा मेल पढ़ना है? नंबर बताइए।",
#     "te-IN": "ఏ మెయిల్ చదవాలి? నంబర్ చెప్పండి.",
# }

# FALLBACK_RESPONSE = {
#     "en-IN": "Sorry, I did not understand. Please try again.",
#     "hi-IN": "माफ़ कीजिए, मैं समझ नहीं पाया। दोबारा कोशिश करें।",
#     "te-IN": "క్షమించండి, నేను అర్థం చేసుకోలేకపోయాను. మళ్ళీ చెప్పండి.",
# }

# ASK_RECIPIENT = {
#     "en-IN": "Who should I send the email to?",
#     "hi-IN": "ईमेल किसे भेजना है?",
#     "te-IN": "ఈ మెయిల్ ఎవరికి పంపాలి?",
# }

# ASK_SUBJECT = {
#     "en-IN": "What is the subject of the email?",
#     "hi-IN": "ईमेल का विषय क्या है?",
#     "te-IN": "మెయిల్ సబ్జెక్ట్ ఏమిటి?",
# }

# ASK_INTENT = {
#     "en-IN": "Please tell me in one sentence what the email should say.",
#     "hi-IN": "एक वाक्य में बताइए कि ईमेल में क्या लिखना है।",
#     "te-IN": "మెయిల్‌లో ఏమి చెప్పాలో ఒక వాక్యంలో చెప్పండి.",
# }

# ASK_REPLY_INTENT = {
#     "en-IN": "What should I reply?",
#     "hi-IN": "क्या जवाब देना है?",
#     "te-IN": "ఏమి జవాబు ఇవ్వాలి?",
# }

# CONFIRM_EMAIL_CREATED = {
#     "en-IN": "I have created the email. Do you want to send it, rewrite it, or cancel?",
#     "hi-IN": "ईमेल तैयार हो गई है। क्या भेजना है, दोबारा लिखना है, या रद्द करना है?",
#     "te-IN": "మెయిల్ తయారైంది. పంపాలా, మళ్ళీ రాయాలా, లేదా రద్దు చేయాలా?",
# }

# ASK_PIN = {
#     "en-IN": "Please provide your four digit security pin.",
#     "hi-IN": "कृपया अपना चार अंकों का सुरक्षा पिन बताएं।",
#     "te-IN": "దయచేసి మీ నాలుగు అంకెల సెక్యూరిటీ పిన్ చెప్పండి.",
# }

# EMAIL_SENT = {
#     "en-IN": "Email sent successfully.",
#     "hi-IN": "ईमेल सफलतापूर्वक भेजा गया।",
#     "te-IN": "మెయిల్ విజయవంతంగా పంపబడింది.",
# }

# EMAIL_CANCELLED = {
#     "en-IN": "Email cancelled.",
#     "hi-IN": "ईमेल रद्द कर दिया गया।",
#     "te-IN": "మెయిల్ రద్దు చేయబడింది.",
# }

# WRONG_PIN = {
#     "en-IN": "Incorrect pin. Please try again.",
#     "hi-IN": "गलत पिन। कृपया दोबारा बताएं।",
#     "te-IN": "తప్పు పిన్. మళ్ళీ చెప్పండి.",
# }

# NO_EMAILS = {
#     "en-IN": "No emails found.",
#     "hi-IN": "कोई ईमेल नहीं मिला।",
#     "te-IN": "ఎలాంటి మెయిల్స్ లేవు.",
# }

# OPEN_EMAIL_FIRST = {
#     "en-IN": "Please open an email first.",
#     "hi-IN": "पहले कोई ईमेल खोलें।",
#     "te-IN": "ముందు ఒక మెయిల్ తెరవండి.",
# }

# # ---------------------------------------------------------------------------
# # TRIGGER KEYWORD LISTS
# # ---------------------------------------------------------------------------

# SEND_MAIL_TRIGGERS = [
#     "send mail", "send email",
#     "compose mail", "compose email",
#     "write mail", "write email",
#     "send a mail", "send an email",
#     # Hindi
#     "मेल भेजो", "ईमेल भेजो", "मेल लिखो", "ईमेल लिखो",
#     # Telugu
#     "మెయిల్ పంపు", "మెయిల్ రాయి",
# ]

# REPLY_COMMANDS = [
#     "reply", "reply to it", "reply to this", "send reply",
#     # Hindi
#     "जवाब दो", "रिप्लाई करो",
#     # Telugu
#     "జవాబు ఇవ్వు", "రిప్లై చేయి",
# ]

# SMART_EMAIL_QUERIES = [
#     "urgent email", "urgent mails", "urgent mail",
#     "important email", "important mails", "important mail",
#     "emails today", "mails today",
#     "any important mail", "any important email",
#     "do i have urgent mail", "do i have urgent email",
#     "which email needs reply", "which mail needs reply",
#     # Hindi
#     "जरूरी मेल", "महत्वपूर्ण मेल",
#     # Telugu
#     "అర్జెంట్ మెయిల్", "ముఖ్యమైన మెయిల్",
# ]

# INBOX_TRIGGERS = [
#     # Hindi
#     "मेल खोलो", "मेल दिखाओ", "इनबॉक्स खोलो", "मेल",
#     # English
#     "open inbox", "show inbox", "check inbox",
#     "mails", "show emails", "show email", "show mail",
#     "open mail", "check email", "check mail",
#     "read email", "read mail",
#     # Telugu
#     "ఇన్‌బాక్స్", "ఇన్‌బాక్స్ చూపించు",
#     "మెయిల్స్", "చూపించు", "మెయిల్స్ చూపించు",
#     "మెయిల్ చదువు",
# ]


# # ---------------------------------------------------------------------------
# # HELPERS
# # ---------------------------------------------------------------------------

# def extract_email_address(sender: str) -> str:
#     """Extract bare email address from a 'Name <email>' formatted string."""
#     match = re.search(r"<(.+?)>", sender)
#     if match:
#         return match.group(1)
#     return sender


# def extract_number(command: str):
#     """
#     Extract a number from the command.
#     Handles: digits, English words, Hindi words/roman, Telugu words/roman.
#     """
#     text = command.lower().strip()

#     # Direct digit(s)
#     match = re.search(r"\b(\d+)\b", text)
#     if match:
#         return int(match.group(1))

#     # Remove punctuation for cleaner word matching
#     cleaned = re.sub(r"[^\w\s]", " ", text)

#     for word in cleaned.split():
#         if word in NUMBER_MAP:
#             return NUMBER_MAP[word]

#     return None


# def save_summary_to_file(content: str, index: int, lang: str):
#     """Save AI translated + summarized email to a text file."""
#     folder = "summaries"
#     if not os.path.exists(folder):
#         os.makedirs(folder)
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"{folder}/email_{index}_{lang}_{timestamp}.txt"
#     with open(filename, "w", encoding="utf-8") as f:
#         f.write(content)
#     print(f"Saved summary to {filename}")


# # ---------------------------------------------------------------------------
# # MAIN COMMAND PARSER
# # ---------------------------------------------------------------------------

# def parse_command(command: str) -> str:

#     command_raw = command.strip()           # preserve original for PIN check
#     command = command_raw.lower().strip()
#     lang = assistant_state.session_language or "en-IN"

#     print(f"[parse_command] lang={lang} | awaiting_email_selection={assistant_state.awaiting_email_selection} | command='{command}'")

#     # ------------------------------------------------------------------
#     # PRIORITY 1: EMAIL SELECTION (must be checked first so numbers are
#     # not swallowed by any other branch below)
#     # ------------------------------------------------------------------
#     if assistant_state.awaiting_email_selection:

#         index = extract_number(command)

#         print(f"[parse_command] email selection mode | extracted index={index}")

#         if index is None:
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         if index < 1 or index > len(assistant_state.email_list):
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         email_meta = assistant_state.email_list[index - 1]

#         from app.services.gmail_service import get_email_details

#         email = get_email_details(
#             assistant_state.user_email,
#             email_meta["id"]
#         )

#         if not email:
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         # Store email in state BEFORE clearing awaiting flag
#         assistant_state.current_email = email
#         assistant_state.current_email_index = index
#         assistant_state.awaiting_email_selection = False

#         # Print full original email in terminal
#         print("\n------ ORIGINAL EMAIL ------")
#         print(email)
#         print("----------------------------\n")

#         # AI Translation + Summarization
#         ai_response = translate_and_summarize(email, lang)

#         # Print AI result
#         print("\n------ AI TRANSLATED + SUMMARY ------")
#         print(ai_response)
#         print("-------------------------------------\n")

#         # Save to file
#         save_summary_to_file(ai_response, index, lang)

#         return ai_response

#     # ------------------------------------------------------------------
#     # PRIORITY 2: PIN VERIFICATION (check raw command to preserve digits)
#     # ------------------------------------------------------------------
#     if assistant_state.awaiting_pin:

#         pin_attempt = re.sub(r"\D", "", command_raw)   # strip non-digits

#         if pin_attempt == assistant_state.user_pin:

#             send_email(
#                 assistant_state.user_email,
#                 assistant_state.recipient,
#                 assistant_state.subject,
#                 assistant_state.generated_email
#             )

#             assistant_state.reset()
#             return EMAIL_SENT.get(lang, EMAIL_SENT["en-IN"])

#         else:
#             return WRONG_PIN.get(lang, WRONG_PIN["en-IN"])

#     # ------------------------------------------------------------------
#     # PRIORITY 3: AWAITING CONFIRMATION (send / rewrite / cancel)
#     # ------------------------------------------------------------------
#     if assistant_state.awaiting_confirmation:

#         if any(w in command for w in ["send", "भेजो", "పంపు"]):
#             assistant_state.awaiting_confirmation = False
#             assistant_state.awaiting_pin = True
#             return ASK_PIN.get(lang, ASK_PIN["en-IN"])

#         if any(w in command for w in ["rewrite", "change", "दोबारा", "మళ్ళీ"]):
#             assistant_state.awaiting_intent = True
#             assistant_state.awaiting_confirmation = False
#             return ASK_INTENT.get(lang, ASK_INTENT["en-IN"])

#         if any(w in command for w in ["cancel", "stop", "रद्द", "రద్దు"]):
#             assistant_state.reset()
#             return EMAIL_CANCELLED.get(lang, EMAIL_CANCELLED["en-IN"])

#         # User said something else — re-ask
#         return CONFIRM_EMAIL_CREATED.get(lang, CONFIRM_EMAIL_CREATED["en-IN"])

#     # ------------------------------------------------------------------
#     # PRIORITY 4: SEND MAIL FLOW — step-by-step capture
#     # ------------------------------------------------------------------

#     # Step: capture intent (used for both new email and reply)
#     if assistant_state.awaiting_intent:

#         assistant_state.intent_line = command_raw
#         assistant_state.awaiting_intent = False

#         if assistant_state.current_email:
#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject": "Re: " + assistant_state.current_email["subject"],
#                 "intent": assistant_state.intent_line,
#                 "context": assistant_state.current_email["body"]
#             })
#         else:
#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject": assistant_state.subject,
#                 "intent": assistant_state.intent_line
#             })

#         assistant_state.generated_email = result["generated_email"]

#         print("\nEMAIL TEMPLATE\n")
#         print(assistant_state.generated_email)

#         assistant_state.awaiting_confirmation = True
#         return CONFIRM_EMAIL_CREATED.get(lang, CONFIRM_EMAIL_CREATED["en-IN"])

#     # Step: capture subject
#     if assistant_state.send_mail_mode and assistant_state.awaiting_subject:

#         assistant_state.subject = command_raw
#         assistant_state.awaiting_subject = False
#         assistant_state.awaiting_intent = True
#         return ASK_INTENT.get(lang, ASK_INTENT["en-IN"])

#     # Step: capture recipient
#     if assistant_state.send_mail_mode and assistant_state.awaiting_recipient:

#         assistant_state.recipient = command_raw
#         assistant_state.awaiting_recipient = False
#         assistant_state.awaiting_subject = True
#         return ASK_SUBJECT.get(lang, ASK_SUBJECT["en-IN"])

#     # ------------------------------------------------------------------
#     # PRIORITY 5: REPLY COMMAND
#     # ------------------------------------------------------------------
#     if any(x in command for x in REPLY_COMMANDS):

#         if not assistant_state.current_email:
#             return OPEN_EMAIL_FIRST.get(lang, OPEN_EMAIL_FIRST["en-IN"])

#         sender = assistant_state.current_email["sender"]
#         assistant_state.recipient = extract_email_address(sender)
#         assistant_state.send_mail_mode = True
#         assistant_state.awaiting_intent = True
#         return ASK_REPLY_INTENT.get(lang, ASK_REPLY_INTENT["en-IN"])

#     # ------------------------------------------------------------------
#     # PRIORITY 6: SMART EMAIL ANALYSIS
#     # ------------------------------------------------------------------
#     if any(q in command for q in SMART_EMAIL_QUERIES):

#         emails = fetch_recent_primary_emails(assistant_state.user_email)

#         if not emails:
#             return NO_EMAILS.get(lang, NO_EMAILS["en-IN"])

#         analysis = analyze_emails(emails)
#         return analysis

#     # ------------------------------------------------------------------
#     # PRIORITY 7: SEND EMAIL — full info in one shot (NLU path)
#     # ------------------------------------------------------------------
#     if any(trigger in command for trigger in SEND_MAIL_TRIGGERS):

#         # Try to extract all fields from the single utterance first
#         parsed = understand_email_request(command_raw)

#         if parsed.get("recipient"):
#             assistant_state.recipient = parsed["recipient"]

#         if parsed.get("subject"):
#             assistant_state.subject = parsed["subject"]

#         if parsed.get("intent"):
#             assistant_state.intent_line = parsed["intent"]

#         # If all three fields are present, generate immediately
#         if (assistant_state.recipient
#                 and assistant_state.subject
#                 and assistant_state.intent_line):

#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject": assistant_state.subject,
#                 "intent": assistant_state.intent_line
#             })

#             assistant_state.generated_email = result["generated_email"]
#             assistant_state.awaiting_confirmation = True
#             return CONFIRM_EMAIL_CREATED.get(lang, CONFIRM_EMAIL_CREATED["en-IN"])

#         # Otherwise start step-by-step flow
#         assistant_state.send_mail_mode = True

#         if not assistant_state.recipient:
#             assistant_state.awaiting_recipient = True
#             return ASK_RECIPIENT.get(lang, ASK_RECIPIENT["en-IN"])

#         if not assistant_state.subject:
#             assistant_state.awaiting_subject = True
#             return ASK_SUBJECT.get(lang, ASK_SUBJECT["en-IN"])

#         assistant_state.awaiting_intent = True
#         return ASK_INTENT.get(lang, ASK_INTENT["en-IN"])

#     # ------------------------------------------------------------------
#     # PRIORITY 8: OPEN INBOX
#     # ------------------------------------------------------------------
#     if any(x in command for x in INBOX_TRIGGERS):

#         emails = fetch_recent_primary_emails(assistant_state.user_email)

#         if not emails:
#             return NO_EMAILS.get(lang, NO_EMAILS["en-IN"])

#         # Store in state
#         assistant_state.email_list = emails
#         assistant_state.awaiting_email_selection = True

#         # Print senders in terminal for debugging
#         print("\n---- EMAIL SENDERS ----")
#         for i, mail in enumerate(emails, 1):
#             print(f"{i}. {mail['sender']}")
#         print("-----------------------\n")

#         response = INTRO_TEXT.get(lang, INTRO_TEXT["en-IN"]) + " "

#         for i, mail in enumerate(emails, 1):
#             if lang == "hi-IN":
#                 response += f"{i} नंबर मेल {mail['sender']} से। "
#             elif lang == "te-IN":
#                 response += f"{i} నంబర్ మెయిల్ {mail['sender']} నుండి. "
#             else:
#                 response += f"Email {i} from {mail['sender']}. "

#         response += ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         return response

#     # ------------------------------------------------------------------
#     # DEFAULT FALLBACK
#     # ------------------------------------------------------------------
#     return FALLBACK_RESPONSE.get(lang, FALLBACK_RESPONSE["en-IN"])


# import re
# import os
# from datetime import datetime

# from app.services.gmail_service import (
#     fetch_recent_primary_emails,
#     send_email,
# )

# from app.utils.conversational_state import assistant_state
# from app.ai.email_understanding import understand_email_request
# from app.ai.groq_service import translate_and_summarize
# from app.ai.email_agent import email_agent
# from app.ai.email_analyzer import analyze_emails


# # ── Number map ─────────────────────────────────────────────────────────────
# # IMPORTANT: "do" removed — it clashes with English "do i have urgent mail"
# # and other sentences. Use only unambiguous words.

# NUMBER_MAP = {
#     # English
#     "one": 1, "first": 1,
#     "two": 2, "second": 2,
#     "three": 3, "third": 3,
#     "four": 4, "fourth": 4,
#     "five": 5, "fifth": 5,

#     # Hindi native
#     "एक": 1, "पहला": 1, "पहले": 1,
#     "दो": 2, "दूसरा": 2,
#     "तीन": 3, "तीसरा": 3,
#     "चार": 4, "चौथा": 4,
#     "पांच": 5, "पांचवा": 5,

#     # Hindi roman (removed "do"/"dho" — too ambiguous in English sentences)
#     "ek": 1, "pehla": 1,
#     "dusra": 2,
#     "teen": 3, "teesra": 3,
#     "char": 4,
#     "paanch": 5,

#     # Telugu native
#     "ఒకటి": 1, "మొదటి": 1,
#     "రెండు": 2, "రెండవ": 2,
#     "మూడు": 3, "మూడవ": 3,
#     "నాలుగు": 4,
#     "ఐదు": 5,

#     # Telugu roman
#     "okati": 1, "modati": 1,
#     "rendu": 2, "rendava": 2,
#     "moodu": 3, "moodava": 3,
#     "nalugu": 4,
#     "aidu": 5,
# }


# # ── Static response strings ────────────────────────────────────────────────

# INTRO_TEXT = {
#     "en-IN": "Here are your latest emails.",
#     "hi-IN": "ये आपके हाल के ईमेल हैं।",
#     "te-IN": "ఇవి మీ తాజా మెయిల్స్.",
# }

# ASK_NUMBER = {
#     "en-IN": "Which email should I read? Please say a number between 1 and 5.",
#     "hi-IN": "कौन सा मेल पढ़ना है? एक से पांच के बीच नंबर बताइए।",
#     "te-IN": "ఏ మెయిల్ చదవాలి? 1 నుండి 5 మధ్య నంబర్ చెప్పండి.",
# }

# FALLBACK_RESPONSE = {
#     "en-IN": "Sorry, I did not understand. Please try again.",
#     "hi-IN": "माफ़ कीजिए, मैं समझ नहीं पाया। दोबारा कोशिश करें।",
#     "te-IN": "క్షమించండి, నేను అర్థం చేసుకోలేకపోయాను. మళ్ళీ చెప్పండి.",
# }

# ASK_RECIPIENT = {
#     "en-IN": "Who should I send the email to?",
#     "hi-IN": "ईमेल किसे भेजना है?",
#     "te-IN": "ఈ మెయిల్ ఎవరికి పంపాలి?",
# }

# ASK_SUBJECT = {
#     "en-IN": "What is the subject of the email?",
#     "hi-IN": "ईमेल का विषय क्या है?",
#     "te-IN": "మెయిల్ సబ్జెక్ట్ ఏమిటి?",
# }

# ASK_INTENT = {
#     "en-IN": "Please tell me in one sentence what the email should say.",
#     "hi-IN": "एक वाक्य में बताइए कि ईमेल में क्या लिखना है।",
#     "te-IN": "మెయిల్‌లో ఏమి చెప్పాలో ఒక వాక్యంలో చెప్పండి.",
# }

# ASK_REPLY_INTENT = {
#     "en-IN": "What should I reply?",
#     "hi-IN": "क्या जवाब देना है?",
#     "te-IN": "ఏమి జవాబు ఇవ్వాలి?",
# }

# CONFIRM_EMAIL_CREATED = {
#     "en-IN": "I have created the email. Say send, rewrite, or cancel.",
#     "hi-IN": "ईमेल तैयार हो गई है। भेजो, दोबारा लिखो, या रद्द करो।",
#     "te-IN": "మెయిల్ తయారైంది. పంపు, మళ్ళీ రాయి, లేదా రద్దు చేయి.",
# }

# ASK_PIN = {
#     "en-IN": "Please say your four digit security pin.",
#     "hi-IN": "कृपया अपना चार अंकों का सुरक्षा पिन बताएं।",
#     "te-IN": "దయచేసి మీ నాలుగు అంకెల సెక్యూరిటీ పిన్ చెప్పండి.",
# }

# EMAIL_SENT = {
#     "en-IN": "Email sent successfully.",
#     "hi-IN": "ईमेल सफलतापूर्वक भेजा गया।",
#     "te-IN": "మెయిల్ విజయవంతంగా పంపబడింది.",
# }

# EMAIL_CANCELLED = {
#     "en-IN": "Email cancelled.",
#     "hi-IN": "ईमेल रद्द कर दिया गया।",
#     "te-IN": "మెయిల్ రద్దు చేయబడింది.",
# }

# WRONG_PIN = {
#     "en-IN": "Incorrect pin. Please try again.",
#     "hi-IN": "गलत पिन। कृपया दोबारा बताएं।",
#     "te-IN": "తప్పు పిన్. మళ్ళీ చెప్పండి.",
# }

# NO_EMAILS = {
#     "en-IN": "No emails found.",
#     "hi-IN": "कोई ईमेल नहीं मिला।",
#     "te-IN": "ఎలాంటి మెయిల్స్ లేవు.",
# }

# OPEN_EMAIL_FIRST = {
#     "en-IN": "Please open an email first.",
#     "hi-IN": "पहले कोई ईमेल खोलें।",
#     "te-IN": "ముందు ఒక మెయిల్ తెరవండి.",
# }

# NO_USER = {
#     "en-IN": "Error: no user logged in. Please sign in first.",
#     "hi-IN": "त्रुटि: कोई उपयोगकर्ता लॉग इन नहीं है।",
#     "te-IN": "లోపం: ఏ వినియోగదారు లాగిన్ కాలేదు.",
# }


# # ── Trigger keyword lists ──────────────────────────────────────────────────

# SEND_MAIL_TRIGGERS = [
#     "send mail", "send email",
#     "compose mail", "compose email",
#     "write mail", "write email",
#     "send a mail", "send an email",
#     # Hindi
#     "मेल भेजो", "ईमेल भेजो", "मेल लिखो", "ईमेल लिखो",
#     # Telugu
#     "మెయిల్ పంపు", "మెయిల్ రాయి",
# ]

# REPLY_COMMANDS = [
#     "reply", "reply to it", "reply to this", "send reply",
#     # Hindi
#     "जवाब दो", "रिप्लाई करो",
#     # Telugu
#     "జవాబు ఇవ్వు", "రిప్లై చేయి",
# ]

# SMART_EMAIL_QUERIES = [
#     "urgent email", "urgent mails", "urgent mail",
#     "important email", "important mails", "important mail",
#     "emails today", "mails today",
#     "any important mail", "any important email",
#     "do i have urgent mail", "do i have urgent email",
#     "which email needs reply", "which mail needs reply",
#     # Hindi
#     "जरूरी मेल", "महत्वपूर्ण मेल",
#     # Telugu
#     "అర్జెంట్ మెయిల్", "ముఖ్యమైన మెయిల్",
# ]

# # NOTE: Removed bare "मेल" because it is too short and matches inside
# # longer Hindi phrases. Only use multi-word or unambiguous triggers.
# INBOX_TRIGGERS = [
#     # Hindi (multi-word or specific)
#     "मेल खोलो", "मेल दिखाओ", "इनबॉक्स खोलो", "इनबॉक्स",
#     # English
#     "open inbox", "show inbox", "check inbox",
#     "show emails", "show email", "show mail",
#     "open mail", "check email", "check mail",
#     "read email", "read mail", "my emails", "my mails",
#     # Telugu
#     "ఇన్‌బాక్స్", "ఇన్‌బాక్స్ చూపించు",
#     "మెయిల్స్", "మెయిల్స్ చూపించు", "మెయిల్ చదువు",
# ]


# # ── Helpers ────────────────────────────────────────────────────────────────

# def extract_email_address(sender: str) -> str:
#     match = re.search(r"<(.+?)>", sender)
#     if match:
#         return match.group(1)
#     return sender


# def extract_number(command: str):
#     """
#     Extract a 1-based index from a voice command.
#     Priority: digit > English word > Hindi word > Telugu word.
#     """
#     text = command.lower().strip()

#     # Digit first — most reliable
#     match = re.search(r"\b([1-9][0-9]?)\b", text)
#     if match:
#         return int(match.group(1))

#     # Strip punctuation then match word tokens
#     cleaned = re.sub(r"[^\w\s]", " ", text)
#     for word in cleaned.split():
#         if word in NUMBER_MAP:
#             return NUMBER_MAP[word]

#     return None


# def save_summary_to_file(content: str, index: int, lang: str):
#     folder = "summaries"
#     if not os.path.exists(folder):
#         os.makedirs(folder)
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"{folder}/email_{index}_{lang}_{timestamp}.txt"
#     with open(filename, "w", encoding="utf-8") as f:
#         f.write(content)
#     print(f"[parser] Saved summary → {filename}")


# # ── Main parser ────────────────────────────────────────────────────────────

# def parse_command(command: str) -> str:

#     command_raw = command.strip()
#     command     = command_raw.lower().strip()
#     lang        = assistant_state.session_language or "en-IN"

#     print(
#         f"[parse_command] lang={lang} | "
#         f"awaiting_email_selection={assistant_state.awaiting_email_selection} | "
#         f"send_mail_mode={assistant_state.send_mail_mode} | "
#         f"command='{command}'"
#     )

#     # Guard: user_email must be set
#     if not assistant_state.user_email:
#         return NO_USER.get(lang, NO_USER["en-IN"])

#     # ── PRIORITY 1: EMAIL SELECTION ────────────────────────────────────
#     # Must be first so digit/word inputs are not swallowed by other branches.
#     if assistant_state.awaiting_email_selection:

#         index = extract_number(command)
#         print(f"[parse_command] email selection → extracted index={index}")

#         if index is None:
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         if index < 1 or index > len(assistant_state.email_list):
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         email_meta = assistant_state.email_list[index - 1]

#         from app.services.gmail_service import get_email_details
#         email = get_email_details(assistant_state.user_email, email_meta["id"])

#         if not email:
#             return ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])

#         assistant_state.current_email       = email
#         assistant_state.current_email_index = index
#         assistant_state.awaiting_email_selection = False

#         print("\n------ ORIGINAL EMAIL ------")
#         print(email)
#         print("----------------------------\n")

#         ai_response = translate_and_summarize(email, lang)

#         print("\n------ AI TRANSLATED + SUMMARY ------")
#         print(ai_response)
#         print("-------------------------------------\n")

#         save_summary_to_file(ai_response, index, lang)
#         return ai_response

#     # ── PRIORITY 2: PIN VERIFICATION ──────────────────────────────────
#     if assistant_state.awaiting_pin:

#         pin_attempt = re.sub(r"\D", "", command_raw)   # keep digits only

#         if pin_attempt == assistant_state.user_pin:
#             send_email(
#                 assistant_state.user_email,
#                 assistant_state.recipient,
#                 assistant_state.subject,
#                 assistant_state.generated_email,
#             )
#             assistant_state.reset()
#             return EMAIL_SENT.get(lang, EMAIL_SENT["en-IN"])

#         return WRONG_PIN.get(lang, WRONG_PIN["en-IN"])

#     # ── PRIORITY 3: AWAITING SEND/REWRITE/CANCEL CONFIRMATION ─────────
#     if assistant_state.awaiting_confirmation:

#         if any(w in command for w in ["send", "भेजो", "పంపు"]):
#             assistant_state.awaiting_confirmation = False
#             assistant_state.awaiting_pin = True
#             return ASK_PIN.get(lang, ASK_PIN["en-IN"])

#         if any(w in command for w in ["rewrite", "change", "दोबारा", "మళ్ళీ"]):
#             assistant_state.awaiting_confirmation = False
#             assistant_state.awaiting_intent = True
#             return ASK_INTENT.get(lang, ASK_INTENT["en-IN"])

#         if any(w in command for w in ["cancel", "stop", "रद्द", "రద్దు"]):
#             assistant_state.reset()
#             return EMAIL_CANCELLED.get(lang, EMAIL_CANCELLED["en-IN"])

#         return CONFIRM_EMAIL_CREATED.get(lang, CONFIRM_EMAIL_CREATED["en-IN"])

#     # ── PRIORITY 4: SEND MAIL STEP CAPTURES ───────────────────────────

#     # Intent capture (new email OR reply)
#     if assistant_state.awaiting_intent:
#         assistant_state.intent_line    = command_raw
#         assistant_state.awaiting_intent = False

#         if assistant_state.current_email:
#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject":   "Re: " + assistant_state.current_email["subject"],
#                 "intent":    assistant_state.intent_line,
#                 "context":   assistant_state.current_email["body"],
#             })
#         else:
#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject":   assistant_state.subject,
#                 "intent":    assistant_state.intent_line,
#             })

#         assistant_state.generated_email      = result["generated_email"]
#         assistant_state.awaiting_confirmation = True

#         print("\nEMAIL TEMPLATE\n")
#         print(assistant_state.generated_email)
#         return CONFIRM_EMAIL_CREATED.get(lang, CONFIRM_EMAIL_CREATED["en-IN"])

#     # Subject capture
#     if assistant_state.send_mail_mode and assistant_state.awaiting_subject:
#         assistant_state.subject         = command_raw
#         assistant_state.awaiting_subject = False
#         assistant_state.awaiting_intent  = True
#         return ASK_INTENT.get(lang, ASK_INTENT["en-IN"])

#     # Recipient capture
#     if assistant_state.send_mail_mode and assistant_state.awaiting_recipient:
#         assistant_state.recipient          = command_raw
#         assistant_state.awaiting_recipient  = False
#         assistant_state.awaiting_subject    = True
#         return ASK_SUBJECT.get(lang, ASK_SUBJECT["en-IN"])

#     # ── PRIORITY 5: REPLY ─────────────────────────────────────────────
#     if any(x in command for x in REPLY_COMMANDS):
#         if not assistant_state.current_email:
#             return OPEN_EMAIL_FIRST.get(lang, OPEN_EMAIL_FIRST["en-IN"])
#         assistant_state.recipient       = extract_email_address(assistant_state.current_email["sender"])
#         assistant_state.send_mail_mode  = True
#         assistant_state.awaiting_intent = True
#         return ASK_REPLY_INTENT.get(lang, ASK_REPLY_INTENT["en-IN"])

#     # ── PRIORITY 6: SMART EMAIL ANALYSIS ──────────────────────────────
#     if any(q in command for q in SMART_EMAIL_QUERIES):
#         emails = fetch_recent_primary_emails(assistant_state.user_email)
#         if not emails:
#             return NO_EMAILS.get(lang, NO_EMAILS["en-IN"])
#         return analyze_emails(emails)

#     # ── PRIORITY 7: NEW EMAIL — NLU single-shot OR step-by-step ───────
#     if any(trigger in command for trigger in SEND_MAIL_TRIGGERS):

#         parsed = understand_email_request(command_raw)

#         if parsed.get("recipient"):
#             assistant_state.recipient = parsed["recipient"]
#         if parsed.get("subject"):
#             assistant_state.subject = parsed["subject"]
#         if parsed.get("intent"):
#             assistant_state.intent_line = parsed["intent"]

#         if assistant_state.recipient and assistant_state.subject and assistant_state.intent_line:
#             result = email_agent.invoke({
#                 "recipient": assistant_state.recipient,
#                 "subject":   assistant_state.subject,
#                 "intent":    assistant_state.intent_line,
#             })
#             assistant_state.generated_email      = result["generated_email"]
#             assistant_state.awaiting_confirmation = True
#             return CONFIRM_EMAIL_CREATED.get(lang, CONFIRM_EMAIL_CREATED["en-IN"])

#         assistant_state.send_mail_mode = True

#         if not assistant_state.recipient:
#             assistant_state.awaiting_recipient = True
#             return ASK_RECIPIENT.get(lang, ASK_RECIPIENT["en-IN"])

#         if not assistant_state.subject:
#             assistant_state.awaiting_subject = True
#             return ASK_SUBJECT.get(lang, ASK_SUBJECT["en-IN"])

#         assistant_state.awaiting_intent = True
#         return ASK_INTENT.get(lang, ASK_INTENT["en-IN"])

#     # ── PRIORITY 8: OPEN INBOX ─────────────────────────────────────────
#     if any(x in command for x in INBOX_TRIGGERS):

#         emails = fetch_recent_primary_emails(assistant_state.user_email)

#         if not emails:
#             return NO_EMAILS.get(lang, NO_EMAILS["en-IN"])

#         assistant_state.email_list               = emails
#         assistant_state.awaiting_email_selection  = True

#         print("\n---- EMAIL SENDERS ----")
#         for i, mail in enumerate(emails, 1):
#             print(f"{i}. {mail['sender']}")
#         print("-----------------------\n")

#         response = INTRO_TEXT.get(lang, INTRO_TEXT["en-IN"]) + " "

#         for i, mail in enumerate(emails, 1):
#             # Use sender name only (strip the <email> part) for cleaner TTS
#             sender_display = re.sub(r"<.*?>", "", mail["sender"]).strip()
#             sender_display = sender_display.strip('"\'') or mail["sender"]

#             if lang == "hi-IN":
#                 response += f"{i} नंबर मेल {sender_display} से। "
#             elif lang == "te-IN":
#                 response += f"{i} నంబర్ మెయిల్ {sender_display} నుండి. "
#             else:
#                 response += f"Email {i} from {sender_display}. "

#         response += ASK_NUMBER.get(lang, ASK_NUMBER["en-IN"])
#         return response

#     # ── FALLBACK ───────────────────────────────────────────────────────
#     return FALLBACK_RESPONSE.get(lang, FALLBACK_RESPONSE["en-IN"])