from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "..")
)

VOICE_UI_PATH = os.path.join(PROJECT_ROOT, "frontend", "voice-ui")

templates = Jinja2Templates(directory=VOICE_UI_PATH)


@router.get("/dashboard")
def dashboard(request: Request):

    username = request.session.get("username")
    email = request.session.get("email")

    if not username:
        return RedirectResponse(url="/login")
    

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "username": username,
            "email": email
        }
    )