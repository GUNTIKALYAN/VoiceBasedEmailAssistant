import speech_recognition as sr
import app.utils.assistant_control as assistant_control
from app.utils.conversational_state import assistant_state
recognizer = sr.Recognizer()

SUPPORTED_LANGUAGES = ["en-IN", "hi-IN", "te-IN"]


def speech_to_text(language=None):

    if assistant_control.exit_requested:
        return None, None
    
    with sr.Microphone() as source:

        print("Listening...")

        recognizer.pause_threshold = 1.5   # wait after speech
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        
        recognizer.adjust_for_ambient_noise(source, duration=0.3)

        try:
            audio = recognizer.listen(
                source,
                timeout=2,
                phrase_time_limit=5
            )
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return None, None
        
    if assistant_control.exit_requested:
        return None, None
        
        # FIXED LANGUAGE MODE
    # if language:
    #     is_login_phase = assistant_state.user_email is None

    #     try:
    #         if is_login_phase:
    #             text = recognizer.recognize_google(audio, language="en-IN")
    #         else:
    #             text = recognizer.recognize_google(audio, language=assistant_state.session_language)
    #             print(f"Recognized ({language}):", text)
    #         return text.lower(), language
        
    #     except sr.UnknownValueError:
    #         return None, language

    #     except sr.RequestError:
    #         print("Speech API error")
    #         return None, language

    # # Try multiple languages automatically
    # for lang in SUPPORTED_LANGUAGES:

    #     if assistant_control.exit_requested:
    #         return None, None

    #     try:
    #         text = recognizer.recognize_google(audio, language=lang)
    #         print(f"Recognized ({lang}):", text)
    #         return text.lower(), lang

    #     except sr.UnknownValueError:
    #         continue

    #     except sr.RequestError:
    #         print("Speech API error")
    #         return None, None

    # return None, None
    if assistant_state.user_email is None:
        lang = "en-IN"   # force English for login
    else:
        lang = assistant_state.session_language or "en-IN"

    # STEP 2: Recognize
    try:
        text = recognizer.recognize_google(audio, language=lang)
        print(f"Recognized ({lang}):", text)
        return text.lower(), lang

    except sr.UnknownValueError:
        print("Could not understand audio")
        return None, lang

    except sr.RequestError:
        print("Speech API error")
        return None, None