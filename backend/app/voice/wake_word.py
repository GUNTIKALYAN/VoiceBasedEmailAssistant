WAKE_WORDS = [
    # English
    "hi", "hey", "hello", "assistant",

    # Hindi
    "हेलो", "नमस्ते", "असिस्टेंट",

    # Telugu
    "హలో", "నమస్కారం", "అసిస్టెంట్"
]


def detect_wake_word(text: str) -> bool:
    if not text:
        return False

    # Normalize text
    text = text.lower().strip()
    print("Checking wake word against:", text)

    # Split sentence into individual words
    spoken_words = text.split()

    # Check for exact match only
    for word in WAKE_WORDS:
        if word in spoken_words:
            print("Wake word detected:", word)
            return True

    print("Wake word NOT detected")
    return False