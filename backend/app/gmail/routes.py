from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.services.gmail_service import send_email

router = APIRouter()

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/send-email")
def send_email_api(req: SendEmailRequest, request: Request):

    user_email = request.session.get("email")

    if not user_email:
        return {"error": "Not logged in"}

    send_email(
        user_email,
        req.to,
        req.subject,
        req.body
    )

    return {"status": "sent"}