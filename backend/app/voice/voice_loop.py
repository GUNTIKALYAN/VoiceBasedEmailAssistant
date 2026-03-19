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
    assistant_control.reset_exit()

    return {
        "logs": logs,
        "status": "stopped"
    }


def run_voice_assistant():

    reset_exit()

    print("Voice assistant started...")

    speak("Assistant activated. Say hello to begin.", "en-IN")
    push_log("sys", "Assistant started.")

    active_session = False
    language_selected = False

    while True:

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
            print("RAW TEXT:",text)
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
        print("RAW TEXT:",text)
        push_log("sys", f"RAW TEXT: {text}")

        if not text:
            time.sleep(1)
            continue

        push_log("user", text)

        # EXIT
        if is_exit_command(text):

            msg = EXIT_RESPONSES[lang]
            speak(msg, lang)

            push_log("sys", msg)

            assistant_state.reset()

            return {
                "status": "terminated"
            }

        # NORMAL COMMAND
        response = parse_command(text)

        if response:
            push_log("sys", response)

        # SPEAK
        if response and "I will read the summary:" in response:
            summary = response.split("I will read the summary:")[-1].split("Do you want")[0]
            speak(summary.strip(), lang)
        else:
            speak(response, lang)

        continue


# def run_voice_assistant():

#     reset_exit()

#     print("Voice assistant started...")

#     logs = []

#     speak("Assistant activated. Say hello to begin.", "en-IN")

#     active_session = False
#     language_selected = False

#     while True:

#         # ───────── WAKE MODE ─────────
#         if not active_session:

#             text, _ = speech_to_text()
#             print("RAW TEXT:", text)

#             if not text:
#                 time.sleep(1)
#                 continue

#             logs.append({"type": "user", "text": text})

#             if detect_wake_word(text):
#                 msg = "Please choose language. English, Hindi, or Telugu."
#                 speak(msg, "en-IN")

#                 logs.append({"type": "sys", "text": msg})

#                 active_session = True

#             continue

#         # ───────── LANGUAGE SELECT ─────────
#         if not language_selected:

#             text, _ = speech_to_text()
#             print("RAW TEXT:", text)

#             if not text:
#                 time.sleep(1)
#                 continue

#             logs.append({"type": "user", "text": text})

#             for key, code in LANGUAGE_SELECTION.items():
#                 if key in text.lower():
#                     assistant_state.session_language = code
#                     language_selected = True

#                     msg = LANGUAGE_CONFIRM[code]
#                     speak(msg, code)

#                     logs.append({"type": "sys", "text": msg})

#                     break

#             continue

#         # ───────── COMMAND MODE ─────────
#         lang = assistant_state.session_language

#         text, _ = speech_to_text(lang)
#         print("RAW TEXT:", text)

#         if not text:
#             time.sleep(1)
#             continue

#         logs.append({"type": "user", "text": text})

#         # EXIT
#         if is_exit_command(text):

#             msg = EXIT_RESPONSES[lang]
#             speak(msg, lang)

#             logs.append({"type": "sys", "text": msg})

#             assistant_state.reset()

#             return {
#                 "logs": logs,
#                 "status": "terminated"
#             }

#         # NORMAL COMMAND
#         response = parse_command(text)

#         logs.append({"type": "sys", "text": response})

#         # SPEAK
#         if "I will read the summary:" in response:
#             summary = response.split("I will read the summary:")[-1].split("Do you want")[0]
#             speak(summary.strip(), lang)
#         else:
#             speak(response, lang)

#         # IMPORTANT → return after ONE cycle
#         return {
#             "logs": logs,
#             "status": "running"
#         }


# def run_voice_assistant():

#     reset_exit()   

#     print("Voice assistant started...")

#     logs = []

#     speak("Assistant activated. Say hello to begin.", "en-IN")

#     active_session = False
#     language_selected = False

#     while True:

#         if should_stop():
#             return shutdown(logs)

#         # -------- WAKE MODE --------
#         if not active_session:

#             if should_stop():
#                 return shutdown()

#             text, _ = speech_to_text()
#             print("RAW TEXT:", text)


#             if should_stop():
#                 return shutdown()

#             if not text:
#                 print("No speech detected - retrying...")
#                 time.sleep(2)
#                 continue
#             logs.append({"type":"user","text":text})

#             if detect_wake_word(text):
#                 msg = "Please choose language. English, Hindi, or Telugu."
#                 speak(msg,"en-IN")
#                 logs.append({"type": "sys", "text": msg})

#                 active_session = True

#             continue

#         # -------- LANGUAGE SELECT --------
#         if not language_selected:

#             if should_stop():
#                 return shutdown()

#             text, _ = speech_to_text()
#             print("RAW TEXT", text)

#             if should_stop():
#                 return shutdown()


#             if not text:
#                 print("No speech detected - retrying...")
#                 time.sleep(2)
#                 continue

#             logs.append({"type": "user", "text": text})

#             for key, code in LANGUAGE_SELECTION.items():
#                 if key in text.lower():
#                     assistant_state.session_language = code
#                     language_selected = True
                    
#                     msg = LANGUAGE_CONFIRM[code]
#                     speak(msg, code)

#                     logs.append({"type":"sys","text":msg})

#                     break

#             continue

#         # -------- COMMAND MODE --------
#         lang = assistant_state.session_language

#         if should_stop():
#                 return shutdown()

#         text, _ = speech_to_text(lang)
#         print("RAW TEXT:", text)

#         if should_stop():
#                 return shutdown()

#         if not text:
#             print("No speech detected - retrying...")
#             time.sleep(2)
#             continue
#         logs.append({"type": "user", "text":text})

#         if is_exit_command(text):
#             msg = EXIT_RESPONSES[lang]

#             speak(msg,lang)

#             logs.append({"type": "user", "text": text})

#             assistant_state.reset()

#             return {
#                 "logs": text,
#                 "status": "terminated"
#             }

#         response = parse_command(text)

#         logs.append({"type":"sys", "text":response})

#         # speak(response, lang)
#         if "I will read the summary:" in response:
#             summary = response.split("I will read the summary:")[-1].split("Do you want")[0]
#             speak(summary.strip())
#         else:
#             speak(response, lang)

#         return {
#             "logs":logs,
#             "status": "running"
#         }
# # # from app.voice.stt import speech_to_text
# # # from app.voice.edge_tts import speak
# # # from app.voice.wake_word import detect_wake_word
# # # from app.commands.command_parser import parse_command
# # # from app.utils.conversational_state import assistant_state
# # # import app.utils.assistant_control as assistant_control


# # # EXIT_WORDS = [
# # #     "quit", "stop", "exit",
# # #     "रुको", "बंद करो", "बंद",
# # #     "ఆపు", "aapu", "bandh chey", "stop chey"
# # # ]


# # # EXIT_RESPONSES = {
# # #     "en-IN": "Shutting down assistant. Thank you.",
# # #     "hi-IN": "असिस्टेंट बंद किया जा रहा है। धन्यवाद।",
# # #     "te-IN": "అసిస్టెంట్ ఆపబడుతోంది. ధన్యవాదాలు."
# # # }


# # # LANGUAGE_SELECTION = {
# # #     "english": "en-IN",
# # #     "hindi": "hi-IN",
# # #     "telugu": "te-IN"
# # # }


# # # LANGUAGE_CONFIRM = {
# # #     "en-IN": "Language selected. How can I assist you?",
# # #     "hi-IN": "हिंदी भाषा चुनी गई। मैं आपकी कैसे मदद कर सकता हूँ?",
# # #     "te-IN": "భాష ఎంపికైంది. నేను ఎలా సహాయం చేయగలను?"
# # # }


# # # def is_exit_command(text):
# # #     return any(w in text.lower() for w in EXIT_WORDS)


# # # def should_stop():
# # #     return assistant_control.exit_requested


# # # def shutdown():
# # #     lang = assistant_state.session_language or "en-IN"

# # #     speak(EXIT_RESPONSES[lang], lang)

# # #     assistant_state.reset()
# # #     assistant_control.reset_exit()

# # #     return {
# # #         "recognized_text": "",
# # #         "response": "Assistant stopped"
# # #     }


# # # def run_voice_assistant():

# # #     speak("Assistant activated. Say hello to begin.", "en-IN")

# # #     active_session = False
# # #     language_selected = False

# # #     while True:

# # #         # UI STOP
# # #         if should_stop():
# # #             return shutdown()

# # #         # -------- WAKE MODE --------
# # #         if not active_session:

# # #             if should_stop():
# # #                 return shutdown()

# # #             text, _ = speech_to_text()

# # #             if should_stop():
# # #                 return shutdown()

# # #             if not text:
# # #                 continue

# # #             if detect_wake_word(text):
# # #                 speak(
# # #                     "Please choose language. English, Hindi, or Telugu.",
# # #                     "en-IN"
# # #                 )
# # #                 active_session = True

# # #             continue


# # #         # -------- LANGUAGE SELECT --------
# # #         if not language_selected:

# # #             if should_stop():
# # #                 return shutdown()

# # #             text, _ = speech_to_text()

# # #             if should_stop():
# # #                 return shutdown()

# # #             if not text:
# # #                 continue

# # #             for key, code in LANGUAGE_SELECTION.items():

# # #                 if key in text.lower():
# # #                     assistant_state.session_language = code
# # #                     language_selected = True

# # #                     speak(LANGUAGE_CONFIRM[code], code)
# # #                     break

# # #             continue


# # #         # -------- COMMAND MODE --------
# # #         lang = assistant_state.session_language

# # #         if should_stop():
# # #             return shutdown()

# # #         text, _ = speech_to_text(lang)

# # #         if should_stop():
# # #             return shutdown()

# # #         if not text:
# # #             continue

# # #         if is_exit_command(text):
# # #             return shutdown()

# # #         response = parse_command(text)

# # #         speak(response, lang)


# # from app.voice.stt import speech_to_text
# # from app.voice.edge_tts import speak
# # from app.voice.wake_word import detect_wake_word
# # from app.commands.command_parser import parse_command
# # from app.utils.conversational_state import assistant_state
# # import app.utils.assistant_control as assistant_control
# # import time


# # EXIT_WORDS = [
# #     "quit", "stop", "exit",
# #     "रुको", "बंद करो", "बंद",
# #     "ఆపు", "aapu", "bandh chey", "stop chey"
# # ]


# # EXIT_RESPONSES = {
# #     "en-IN": "Shutting down assistant. Thank you.",
# #     "hi-IN": "असिस्टेंट बंद किया जा रहा है। धन्यवाद।",
# #     "te-IN": "అసిస్టెంట్ ఆపబడుతోంది. ధన్యవాదాలు."
# # }


# # LANGUAGE_SELECTION = {
# #     "english": "en-IN",
# #     "hindi": "hi-IN",
# #     "telugu": "te-IN"
# # }


# # LANGUAGE_CONFIRM = {
# #     "en-IN": "Language selected. How can I assist you?",
# #     "hi-IN": "हिंदी भाषा चुनी गई। मैं आपकी कैसे मदद कर सकता हूँ?",
# #     "te-IN": "భాష ఎంపికైంది. నేను ఎలా సహాయం చేయగలను?"
# # }


# # def is_exit_command(text):
# #     return any(w in text.lower() for w in EXIT_WORDS)


# # def should_stop():
# #     return assistant_control.exit_requested


# # def shutdown():
# #     lang = assistant_state.session_language or "en-IN"
# #     speak(EXIT_RESPONSES[lang], lang)
# #     # Wait for TTS to finish before resetting
# #     time.sleep(2)
# #     assistant_state.reset()
# #     assistant_control.reset_exit()
# #     return {
# #         "recognized_text": "",
# #         "response": "Assistant stopped"
# #     }


# # def speak_and_wait(text: str, lang: str, extra_wait: float = 0.8):
# #     """
# #     Speaks the text and waits for playback to fully complete
# #     before returning control. This prevents STT from opening
# #     the mic while TTS audio is still playing.

# #     extra_wait: additional buffer seconds after estimated speech duration.
# #     """
# #     speak(text, lang)

# #     # Estimate speech duration: ~130 words per minute average for TTS
# #     word_count = len(text.split())
# #     estimated_seconds = (word_count / 130) * 60

# #     # Minimum 1 second, plus buffer
# #     wait_time = max(1.0, estimated_seconds) + extra_wait
# #     time.sleep(wait_time)


# # def run_voice_assistant():

# #     speak_and_wait("Assistant activated. Say hello to begin.", "en-IN")

# #     active_session = False
# #     language_selected = False

# #     while True:

# #         # UI STOP CHECK
# #         if should_stop():
# #             return shutdown()

# #         # -------- WAKE MODE --------
# #         if not active_session:

# #             if should_stop():
# #                 return shutdown()

# #             text, _ = speech_to_text()

# #             if should_stop():
# #                 return shutdown()

# #             if not text:
# #                 continue

# #             if detect_wake_word(text):
# #                 speak_and_wait(
# #                     "Please choose language. English, Hindi, or Telugu.",
# #                     "en-IN"
# #                 )
# #                 active_session = True

# #             continue

# #         # -------- LANGUAGE SELECT --------
# #         if not language_selected:

# #             if should_stop():
# #                 return shutdown()

# #             text, _ = speech_to_text()

# #             if should_stop():
# #                 return shutdown()

# #             if not text:
# #                 continue

# #             for key, code in LANGUAGE_SELECTION.items():

# #                 if key in text.lower():
# #                     assistant_state.session_language = code
# #                     language_selected = True
# #                     speak_and_wait(LANGUAGE_CONFIRM[code], code)
# #                     break

# #             continue

# #         # -------- COMMAND MODE --------
# #         lang = assistant_state.session_language

# #         if should_stop():
# #             return shutdown()

# #         # Use the session language for STT so recognition matches the spoken language
# #         text, _ = speech_to_text(lang)

# #         if should_stop():
# #             return shutdown()

# #         if not text:
# #             continue

# #         if is_exit_command(text):
# #             return shutdown()

# #         print(f"Recognized ({lang}): {text}")

# #         response = parse_command(text)

# #         if response:
# #             # Wait for full TTS playback before listening again.
# #             # For email lists (long responses) add more buffer time.
# #             extra = 1.5 if assistant_state.awaiting_email_selection else 0.8
# #             speak_and_wait(response, lang, extra_wait=extra)

# from app.voice.stt import speech_to_text
# from app.voice.edge_tts import speak
# from app.voice.wake_word import detect_wake_word
# from app.commands.command_parser import parse_command
# from app.utils.conversational_state import assistant_state
# import app.utils.assistant_control as assistant_control
# import time


# EXIT_WORDS = [
#     "quit", "stop", "exit",
#     # Hindi
#     "रुको", "बंद करो", "बंद",
#     # Telugu
#     "ఆపు", "aapu", "bandh chey", "stop chey",
# ]

# EXIT_RESPONSES = {
#     "en-IN": "Shutting down assistant. Thank you.",
#     "hi-IN": "असिस्टेंट बंद किया जा रहा है। धन्यवाद।",
#     "te-IN": "అసిస్టెంట్ ఆపబడుతోంది. ధన్యవాదాలు.",
# }

# LANGUAGE_SELECTION = {
#     "english": "en-IN",
#     "hindi":   "hi-IN",
#     "telugu":  "te-IN",
# }

# LANGUAGE_CONFIRM = {
#     "en-IN": "Language selected. How can I assist you?",
#     "hi-IN": "हिंदी भाषा चुनी गई। मैं आपकी कैसे मदद कर सकता हूँ?",
#     "te-IN": "భాష ఎంపికైంది. నేను ఎలా సహాయం చేయగలను?",
# }


# # ── Helpers ────────────────────────────────────────────────────────────────

# def is_exit_command(text: str) -> bool:
#     return any(w in text.lower() for w in EXIT_WORDS)


# def should_stop() -> bool:
#     return assistant_control.exit_requested


# def speak_and_wait(text: str, lang: str, extra_wait: float = 0.8):
#     """
#     Speak text then block until playback is estimated to be complete.
#     This prevents speech_to_text() from opening the mic while TTS audio
#     is still playing, which was the root cause of missed voice commands.

#     Estimation: ~130 words per minute (average TTS speed).
#     extra_wait: additional buffer seconds after the estimated duration.
#     """
#     speak(text, lang)

#     word_count = len(text.split())
#     estimated_seconds = (word_count / 130) * 60   # 130 wpm -> seconds
#     wait_time = max(1.0, estimated_seconds) + extra_wait
#     time.sleep(wait_time)


# def shutdown() -> dict:
#     lang = assistant_state.session_language or "en-IN"
#     speak_and_wait(EXIT_RESPONSES[lang], lang)
#     assistant_state.reset()
#     assistant_control.reset_exit()
#     return {
#         "recognized_text": "",
#         "response": "Assistant stopped",
#     }


# # ── Main loop ──────────────────────────────────────────────────────────────

# def run_voice_assistant() -> dict:
#     """
#     Blocking voice loop.
#     Expects assistant_state.user_email to already be set by the caller.
#     main.py injects it from the HTTP session before calling this function.
#     """

#     # Safety guard - should never be None at this point
#     if not assistant_state.user_email:
#         return {
#             "recognized_text": "",
#             "response": "Error: user not logged in.",
#         }

#     speak_and_wait("Assistant activated. Say hello to begin.", "en-IN")

#     active_session    = False
#     language_selected = False

#     while True:

#         # ── UI stop requested ──────────────────────────────────────────
#         if should_stop():
#             return shutdown()

#         # ── PHASE 1: WAKE WORD ─────────────────────────────────────────
#         if not active_session:

#             if should_stop():
#                 return shutdown()

#             text, _ = speech_to_text()

#             if should_stop():
#                 return shutdown()

#             if not text:
#                 continue

#             if detect_wake_word(text):
#                 speak_and_wait(
#                     "Please choose language. English, Hindi, or Telugu.",
#                     "en-IN",
#                 )
#                 active_session = True

#             continue

#         # ── PHASE 2: LANGUAGE SELECTION ────────────────────────────────
#         if not language_selected:

#             if should_stop():
#                 return shutdown()

#             text, _ = speech_to_text()

#             if should_stop():
#                 return shutdown()

#             if not text:
#                 continue

#             matched = False
#             for key, code in LANGUAGE_SELECTION.items():
#                 if key in text.lower():
#                     assistant_state.session_language = code
#                     language_selected = True
#                     matched = True
#                     speak_and_wait(LANGUAGE_CONFIRM[code], code)
#                     break

#             # If nothing matched, re-prompt so user is not stuck silently
#             if not matched:
#                 speak_and_wait(
#                     "Sorry, please say English, Hindi, or Telugu.",
#                     "en-IN",
#                 )

#             continue

#         # ── PHASE 3: COMMAND MODE ──────────────────────────────────────
#         lang = assistant_state.session_language

#         if should_stop():
#             return shutdown()

#         # Use the session language for STT for better recognition accuracy
#         text, _ = speech_to_text(lang)

#         if should_stop():
#             return shutdown()

#         if not text:
#             continue

#         if is_exit_command(text):
#             return shutdown()

#         print(f"Recognized ({lang}): {text}")

#         response = parse_command(text)

#         if response:
#             # Give extra buffer after long email-list responses so the user
#             # has time to hear all sender names before mic opens again.
#             extra = 1.5 if assistant_state.awaiting_email_selection else 0.8
#             speak_and_wait(response, lang, extra_wait=extra)


# from app.voice.stt import speech_to_text
# from app.voice.edge_tts import speak
# from app.voice.wake_word import detect_wake_word
# from app.commands.command_parser import parse_command
# from app.utils.conversational_state import assistant_state
# import app.utils.assistant_control as assistant_control
# import threading
# import time


# EXIT_WORDS = [
#     "quit", "stop", "exit",
#     "रुको", "बंद करो", "बंद",
#     "ఆపు", "aapu", "bandh chey", "stop chey",
# ]

# EXIT_RESPONSES = {
#     "en-IN": "Shutting down assistant. Thank you.",
#     "hi-IN": "असिस्टेंट बंद किया जा रहा है। धन्यवाद।",
#     "te-IN": "అసిస్టెంట్ ఆపబడుతోంది. ధన్యవాదాలు.",
# }

# LANGUAGE_SELECTION = {
#     "english": "en-IN",
#     "hindi":   "hi-IN",
#     "telugu":  "te-IN",
# }

# LANGUAGE_CONFIRM = {
#     "en-IN": "Language selected. How can I assist you?",
#     "hi-IN": "हिंदी भाषा चुनी गई। मैं आपकी कैसे मदद कर सकता हूँ?",
#     "te-IN": "భాష ఎంపికైంది. నేను ఎలా సహాయం చేయగలను?",
# }

# # ── Global TTS lock ────────────────────────────────────────────────────────
# # _tts_playing is SET while audio is being spoken.
# # safe_speech_to_text() blocks until it is CLEAR before opening the mic.
# _tts_playing = threading.Event()


# # ── Helpers ────────────────────────────────────────────────────────────────

# def is_exit_command(text: str) -> bool:
#     return any(w in text.lower() for w in EXIT_WORDS)


# def should_stop() -> bool:
#     return assistant_control.exit_requested


# def calculate_tts_wait(text: str, extra_wait: float = 1.0) -> float:
#     """
#     Estimate TTS playback duration from word count (~130 wpm).
#     Minimum 1.5 seconds regardless of text length.
#     """
#     word_count = len(text.split())
#     estimated_seconds = (word_count / 130) * 60
#     return max(1.5, estimated_seconds) + extra_wait


# def speak_and_wait(text: str, lang: str, extra_wait: float = 1.0):
#     """
#     Speak text, then block until playback is estimated to be complete.

#     Flow:
#       1. SET _tts_playing  → mic is locked
#       2. call speak()
#       3. sleep for estimated duration + buffer
#       4. CLEAR _tts_playing → mic is unlocked
#       5. sleep 0.3 s extra so mic hardware fully settles

#     This prevents:
#       - The mic picking up TTS audio as a voice command ("open inbox" echo)
#       - STT opening before TTS finishes (missed number input)
#     """
#     _tts_playing.set()
#     try:
#         speak(text, lang)
#         wait_time = calculate_tts_wait(text, extra_wait)
#         print(f"[TTS] {len(text.split())} words → waiting {wait_time:.1f}s before mic opens")
#         time.sleep(wait_time)
#     finally:
#         _tts_playing.clear()
#         time.sleep(0.3)   # hardware settle gap


# def safe_speech_to_text(lang: str = "en-IN"):
#     """
#     Wait for any active TTS playback to finish, then open the mic.
#     Replaces all direct speech_to_text() calls in the loop.
#     """
#     while _tts_playing.is_set():
#         time.sleep(0.1)
#     return speech_to_text(lang)


# def shutdown() -> dict:
#     lang = assistant_state.session_language or "en-IN"
#     speak_and_wait(EXIT_RESPONSES[lang], lang)
#     assistant_state.reset()
#     assistant_control.reset_exit()
#     return {"recognized_text": "", "response": "Assistant stopped"}


# # ── Main loop ──────────────────────────────────────────────────────────────

# def run_voice_assistant() -> dict:
#     """
#     Blocking voice assistant loop.
#     assistant_state.user_email must already be set by the caller (main.py).
#     """

#     if not assistant_state.user_email:
#         return {"recognized_text": "", "response": "Error: user not logged in."}

#     speak_and_wait("Assistant activated. Say hello to begin.", "en-IN")

#     active_session    = False
#     language_selected = False

#     while True:

#         if should_stop():
#             return shutdown()

#         # ── PHASE 1: WAKE WORD ─────────────────────────────────────────
#         if not active_session:
#             if should_stop():
#                 return shutdown()

#             text, _ = safe_speech_to_text("en-IN")

#             if should_stop():
#                 return shutdown()
#             if not text:
#                 continue

#             if detect_wake_word(text):
#                 speak_and_wait(
#                     "Please choose language. English, Hindi, or Telugu.",
#                     "en-IN",
#                 )
#                 active_session = True
#             continue

#         # ── PHASE 2: LANGUAGE SELECTION ────────────────────────────────
#         if not language_selected:
#             if should_stop():
#                 return shutdown()

#             text, _ = safe_speech_to_text("en-IN")

#             if should_stop():
#                 return shutdown()
#             if not text:
#                 continue

#             matched = False
#             for key, code in LANGUAGE_SELECTION.items():
#                 if key in text.lower():
#                     assistant_state.session_language = code
#                     language_selected = True
#                     matched = True
#                     speak_and_wait(LANGUAGE_CONFIRM[code], code)
#                     break

#             if not matched:
#                 speak_and_wait(
#                     "Sorry, please say English, Hindi, or Telugu.",
#                     "en-IN",
#                 )
#             continue

#         # ── PHASE 3: COMMAND MODE ──────────────────────────────────────
#         lang = assistant_state.session_language

#         if should_stop():
#             return shutdown()

#         text, _ = safe_speech_to_text(lang)

#         if should_stop():
#             return shutdown()
#         if not text:
#             continue

#         if is_exit_command(text):
#             return shutdown()

#         print(f"Recognized ({lang}): {text}")

#         response = parse_command(text)

#         if response:
#             # Email list responses are long — use extra buffer so the user
#             # hears all 5 sender names before the mic opens for number input.
#             extra = 2.0 if assistant_state.awaiting_email_selection else 1.0
#             speak_and_wait(response, lang, extra_wait=extra)
