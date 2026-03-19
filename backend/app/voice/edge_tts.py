import asyncio
import edge_tts
import pygame
import tempfile
import os

pygame.mixer.init()

VOICE_MAP = {
    "en-IN": "en-IN-NeerjaNeural",
    "hi-IN": "hi-IN-SwaraNeural",
    "te-IN": "te-IN-ShrutiNeural"
}


async def speak_async(text: str, language="en-IN"):

    voice = VOICE_MAP.get(language, VOICE_MAP["en-IN"])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_audio = f.name

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(temp_audio)

    pygame.mixer.music.load(temp_audio)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    pygame.mixer.music.unload()
    os.remove(temp_audio)


def speak(text: str, language="en-IN"):
    asyncio.run(speak_async(text, language))

# Test
if __name__ == "__main__":
    speak("Hello, this is English voice", "english")
    speak("Aap kaise ho, aaj meeting kab hai", "hindi")
    speak("Namaskaram Idhi Telugu", "telugu")