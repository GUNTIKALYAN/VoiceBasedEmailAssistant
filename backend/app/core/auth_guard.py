from fastapi import Request, HTTPException
from app.db import user_auth_collection

def require_user(request: Request):
    email = request.session.get("email")

    if not email:
        raise HTTPException(status_code=401, detail="Not logged in")

    user = user_auth_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔥 Block if password not set
    if not user.get("has_password"):
        raise HTTPException(
            status_code=403,
            detail="Password setup required"
        )

    return user