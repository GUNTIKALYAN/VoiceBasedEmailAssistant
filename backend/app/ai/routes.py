from fastapi import APIRouter
from pydantic import BaseModel
from app.ai.email_suggester import generate_suggestion

router = APIRouter()

class SuggestRequest(BaseModel):
    text: str

@router.post("/email/suggest")
def suggest(req: SuggestRequest):

    suggestion = generate_suggestion(req.text)

    return {
        "suggestion": suggestion
    }