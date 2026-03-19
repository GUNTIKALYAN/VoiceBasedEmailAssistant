def normalize_pin(text: str) -> str:

    text = str(text).lower().strip()

    mapping = {
        "zero": "0", "one": "1", "two": "2", "three": "3",
        "four": "4", "five": "5", "six": "6",
        "seven": "7", "eight": "8", "nine": "9",
    }

    words = text.split()
    digits = []

    for w in words:
        if w in mapping:
            digits.append(mapping[w])
        else:
            # extract digits inside string
            extracted = "".join([c for c in w if c.isdigit()])
            if extracted:
                digits.append(extracted)

    return "".join(digits)

def normalize_email_username(text: str):
    text = str(text).lower().strip()

    words = text.split()

    noise_words = {"at", "dot", "gmail", "email", "id"}

    filtered = [w for w in words if w not in noise_words]

    return "".join(filtered)

def normalize_confirmation(text: str) -> str:
    text = str(text).strip().lower()

    yes_words = ["yes", "yeah", "ok", "okay", "correct"]
    no_words = ["no", "not", "wrong", "incorrect"]

    # 🔥 check NO first
    if any(word in text for word in no_words):
        return "no"

    # THEN YES
    if any(word in text for word in yes_words):
        return "yes"

    return "unknown"


def normalize_email_full(text: str):

    text = str(text).lower().strip()

    # ─────────────────────────────
    # STEP 1: Replace common speech patterns
    # ─────────────────────────────
    replacements = {
        " at the rate ": "@",
        " at rate ": "@",
        " at ": "@",
        " dot ": ".",
        " dt ": ".",
        " underscore ": "_",
        " dash ": "-",
        " hyphen ": "-",
        " space ": "",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    # remove spaces completely
    text = text.replace(" ", "")

    # ─────────────────────────────
    # STEP 2: Fix common domains
    # ─────────────────────────────
    if "@gmailcom" in text:
        text = text.replace("@gmailcom", "@gmail.com")

    if "@gamil.com" in text:
        text = text.replace("@gamil.com", "@gmail.com")

    if "@gmail" in text and not text.endswith(".com"):
        text = text + ".com"

    # ─────────────────────────────
    # STEP 3: If no domain → default
    # ─────────────────────────────
    if "@" not in text:
        text = text + "@gmail.com"

    return text

import re

def extract_name_from_email(email: str):

    username = email.split("@")[0]

    # remove digits
    username = re.sub(r"\d+", "", username)

    # split based on common patterns (basic)
    # you can improve later
    name_parts = re.findall('[a-zA-Z]+', username)

    if not name_parts:
        return "there"

    # capitalize each part
    name = " ".join(part.capitalize() for part in name_parts)

    return name
