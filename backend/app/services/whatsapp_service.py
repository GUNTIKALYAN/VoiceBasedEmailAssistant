from datetime import datetime
from app.db import db

import requests
import os

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = "whatsapp:+14155238886"  


whatsapp_collection = db["whatsapp_messages"]

def save_incoming_message(data: dict):

    print("Saving to DB:", data)
    print("DB NAME:", db.name)

    whatsapp_collection.insert_one({
        "from": data.get("from"),
        "name": data.get("name", "Unknown"),
        "body": data.get("body"),
        "timestamp": datetime.utcnow()
    })


def fetch_recent_whatsapp_messages(limit=5):

    messages = whatsapp_collection.find().sort("timestamp", -1).limit(limit)

    result = []
    for msg in messages:
        print("DB MESSAGE:",msg)
        result.append({
            "sender": msg.get("name"),
            "snippet": msg.get("body"),
            "from": msg.get("from"),
            "id": str(msg.get("_id"))
        })
    print("FINAL RESULT:", result)

    return result



def send_whatsapp_message(to_number: str, message: str):

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"

    data = {
        "From": TWILIO_NUMBER,
        "To": to_number,
        "Body": message
    }

    response = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_AUTH))

    print("📤 WhatsApp Sent:", response.status_code, response.text)

    return response.status_code == 201