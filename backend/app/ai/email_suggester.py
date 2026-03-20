from app.ai.groq_service import run_llm


def generate_suggestion(text: str) -> str:
    """
    Generate next-word / next-phrase suggestion for email writing
    """

    # Safety check
    if not text or len(text.strip()) < 3:
        return ""

    prompt = f"""
You are a smart email writing assistant.

Continue the following email naturally and professionally.

STRICT RULES:
- Only return the next continuation
- Maximum 8–12 words
- Do NOT repeat the input
- Do NOT add greetings again
- Do NOT explain anything
- No quotes

Email so far:
{text}
"""

    try:
        suggestion = run_llm(prompt)

        # Clean response (important)
        suggestion = suggestion.strip().replace("\n", " ")

        # Optional: cut long outputs
        words = suggestion.split()
        if len(words) > 12:
            suggestion = " ".join(words[:12])

        return suggestion

    except Exception as e:
        print("Suggestion Error:", str(e))
        return ""