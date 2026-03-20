from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter()

from app.services.whatsapp_service import save_incoming_message

@router.post("/whatsapp/webhook")
@router.post("/whatsapp/webhook/")
async def whatsapp_webhook(request: Request):

    form = await request.form()
    data = dict(form)

    print("🔥 WEBHOOK HIT")
    print("🔥 DATA:", data)

    print("CALLING SAVE FUNCTION")


    save_incoming_message({
        "from": data.get("From"),
        "name": data.get("ProfileName") or data.get("From"),
        "body": data.get("Body")
    })

    return PlainTextResponse("OK")