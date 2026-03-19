import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read API key and model from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables.")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)



# TRANSLATE + SUMMARIZE EMAIL
def translate_and_summarize(email: dict, language: str) -> str:

    language_map = {
        "en-IN": "English",
        "hi-IN": "Hindi",
        "te-IN": "Telugu"
    }

    target_language = language_map.get(language, "English")

    email_content = f"""
Sender: {email.get('sender', '')}
Subject: {email.get('subject', '')}
Body: {email.get('snippet', '')}
"""

    prompt = f"""
You are an AI email assistant.

Your job is to translate and summarize the email.

TARGET LANGUAGE: {target_language}

STRICT LANGUAGE RULES:

If target language is English:
- Output must be ONLY English.
- Do NOT include Hindi or Telugu.

If target language is Hindi:
- Output must be ONLY Hindi written in Devanagari script.

If target language is Telugu:
- Output must be ONLY Telugu written in Telugu script.

DO NOT mix languages.

TASK:
Produce ONLY two sections.

Main Purpose:
(one sentence)

Summary:
(maximum 3 short lines)

Do NOT include:
- Original email
- Translated email body
- URLs
- Repeated text
- Extra headings

EMAIL INPUT:
{email_content}
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Groq API Error:", str(e))

        fallback = {
            "en-IN": "Sorry, I couldn't summarize this email.",
            "hi-IN": "क्षमा करें, मैं इस ईमेल का सारांश नहीं बना पाया।",
            "te-IN": "క్షమించండి, ఈ మెయిల్‌ను సంక్షిప్తంగా చెప్పలేకపోయాను."
        }

        return fallback.get(language, fallback["en-IN"])
    

# GENERIC LLM PROMPT
def run_llm(prompt: str) -> str:

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Groq API Error:", str(e))
        return "Sorry, I couldn't process that request."