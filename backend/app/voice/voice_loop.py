from app.voice.stt import speech_to_text
from app.voice.edge_tts import speak
from app.voice.wake_word import detect_wake_word
from app.commands.command_parser import parse_command
from app.utils.conversational_state import assistant_state
import app.utils.assistant_control as assistant_control
from app.utils.assistant_control import reset_exit
from collections import deque

LIVE_LOGS = deque(maxlen=100)

def push_log(log_type, text):
    entry = {
        "type": log_type,
        "text": text
    }
    LIVE_LOGS.append(entry)
    print(f"[{log_type.upper()}] {text}")  # still keep terminal logs
    
import time
EXIT_WORDS = [
    "quit", "stop", "exit",
    "रुको", "बंद करो", "बंद",
    "ఆపు", "aapu", "bandh chey", "stop chey"
]


EXIT_RESPONSES = {
    "en-IN": "Shutting down assistant. Thank you.",
    "hi-IN": "असिस्टेंट बंद किया जा रहा है। धन्यवाद।",
    "te-IN": "అసిస్టెంట్ ఆపబడుతోంది. ధన్యవాదాలు."
}


LANGUAGE_SELECTION = {
    "english": "en-IN",
    "hindi": "hi-IN",
    "telugu": "te-IN"
}


LANGUAGE_CONFIRM = {
    "en-IN": "Language selected. How can I assist you?",
    "hi-IN": "हिंदी भाषा चुनी गई। मैं आपकी कैसे मदद कर सकता हूँ?",
    "te-IN": "భాష ఎంపికైంది. నేను ఎలా సహాయం చేయగలను?"
}


def is_exit_command(text):
    return any(w in text.lower() for w in EXIT_WORDS)


def should_stop():
    return assistant_control.exit_requested

def shutdown(logs):
    lang = assistant_state.session_language or "en-IN"

    msg = EXIT_RESPONSES[lang]

    speak(msg, lang)

    push_log("user",msg)

    assistant_state.reset()

    assistant_control.exit_requested = False
    assistant_control.reset_exit()

    return {
        "logs": logs,
        "status": "stopped"
    }


def run_voice_assistant():

    global assistant_running

    assistant_control.exit_requested = False
    reset_exit()

    print("Voice assistant started...")

    speak("Assistant activated. Say hello to begin.", "en-IN")
    push_log("sys", "Assistant started.")

    active_session = False
    language_selected = False

    try:
        while True:

            # 🔴 STOP CHECK (IMPORTANT)
            if should_stop():
                push_log("sys", "Assistant stopped.")
                speak("Assistant stopped.", assistant_state.session_language or "en-IN")
                break

            # ───────── WAKE MODE ─────────
            if not active_session:

                push_log("sys", "Listening...")

                text, _ = speech_to_text()
                push_log("sys", f"RAW TEXT: {text}")

                if not text:
                    time.sleep(1)
                    continue

                push_log("user", text)

                if detect_wake_word(text):
                    msg = "Please choose language. English, Hindi, or Telugu."
                    speak(msg, "en-IN")
                    push_log("sys", msg)

                    active_session = True

                continue

            # ───────── LANGUAGE SELECT ─────────
            if not language_selected:

                push_log("sys", "Listening...")

                text, _ = speech_to_text()
                push_log("sys", f"RAW TEXT: {text}")

                if not text:
                    time.sleep(1)
                    continue

                push_log("user", text)

                for key, code in LANGUAGE_SELECTION.items():
                    if key in text.lower():
                        assistant_state.session_language = code
                        language_selected = True

                        msg = LANGUAGE_CONFIRM[code]
                        speak(msg, code)
                        push_log("sys", msg)

                        break

                continue

            # ───────── COMMAND MODE ─────────
            lang = assistant_state.session_language

            push_log("sys", "Listening...")

            text, _ = speech_to_text(lang)
            push_log("sys", f"RAW TEXT: {text}")

            if not text:
                time.sleep(1)
                continue

            push_log("user", text)

            # 🔴 EXIT COMMAND
            if is_exit_command(text):

                msg = EXIT_RESPONSES[lang]
                speak(msg, lang)

                push_log("sys", msg)

                assistant_state.reset()
                break   # ✅ NOT return

            # ───────── NORMAL COMMAND ─────────
            response = parse_command(text)

            if response:
                push_log("sys", response)

                # SPEAK LOGIC
                if "I will read the summary:" in response:
                    summary = response.split("I will read the summary:")[-1].split("Do you want")[0]
                    speak(summary.strip(), lang)
                else:
                    speak(response, lang)

    except Exception as e:
        print("Voice loop error:", e)
        push_log("error", str(e))

    finally:
        assistant_running = False
        assistant_control.exit_requested = False
        print("Assistant loop ended")

