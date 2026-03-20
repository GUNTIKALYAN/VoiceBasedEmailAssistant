from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from datetime import datetime

from app.db import user_auth_collection
from .models import UserSignup, UserLogin
from .utils import hash_password, verify_password
from pydantic import BaseModel

from app.core.google_oauth import oauth
from app.utils.conversational_state import assistant_state

from datetime import datetime
from fastapi import Request, APIRouter
from app.db import user_auth_collection
from app.utils.voice_utils import normalize_pin, normalize_email_username
from app.auth.utils import hash_pin, verify_pin



import os

class AdminLogin(BaseModel):
    email:str
    password: str
    admin_key: str


ADMIN_EMAILS = [
    "admin@voxmail.com",
    "admin2@voxmail.com",
    "admin3@voxmail.com"
]

ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "4321")

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# SIGNUP
@router.post("/signup")
def signup(user: UserSignup):

    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password too long (max 72 bytes for bcrypt)"
        )

    existing_user = user_auth_collection.find_one({
        "email": user.email
    })

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    hashed_pwd = hash_password(user.password)

    user_auth_collection.insert_one({
        "username": user.username,
        "email": user.email,
        "password": hashed_pwd,

        "voice_pin": None,
        "has_voice_pin": False,

        "provider":"local",
        "google_token": None,

        "role": "user",
        "created_at": datetime.utcnow()
    })

    return {"message": "User created successfully"}


# LOGIN
@router.post("/login")
def login(user: UserLogin, request: Request):

    db_user = user_auth_collection.find_one({
        "email": user.email
    })

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check if user is blocked
    if db_user.get("status") == "blocked":
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked. Contact admin@voxmail.com"
        )

    
    if db_user["provider"] == "google" and not db_user.get("has_password"):
        raise HTTPException(
            status_code=400,
            detail="Please login using Google or set a password first"
        )

    if not verify_password(
        user.password,
        db_user["password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    # Save session
    request.session["username"] = db_user["username"]
    request.session["email"] = db_user["email"]

    assistant_state.user_email = db_user["email"]

    return RedirectResponse(
        url="/dashboard",
        status_code=303
    )

@router.get("/google/login")
async def google_login(request: Request):

    request.session["next"] = request.query_params.get("next", "/dashboard")


    redirect_uri = request.url_for("google_callback")

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent"
    )


@router.get("/google/callback")
async def google_callback(request: Request):

    token = await oauth.google.authorize_access_token(request)

    resp = await oauth.google.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        token=token
    )

    user_info = resp.json()

    if not user_info.get("verified_email"):
        raise HTTPException(
            status_code=400,
            detail="Google email not verified"
        )

    email = user_info["email"]
    username = user_info.get("name", email.split("@")[0])

    existing_user = user_auth_collection.find_one({"email": email})

    if existing_user and existing_user.get("status") == "blocked":
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked. Contact admin@voxmail.com"
        )

    if existing_user:

        # update existing user with Google login
        user_auth_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "provider": "google",
                    "google_token": token,
                }
            }
        )

    else:

        # create new Google user
        user_auth_collection.insert_one({
            "username": username,
            "email": email,
            "password": None,
            "has_password":False,
            "voice_pin": None,
            "has_voice_pin": False,
            "provider": "google",
            "google_token": token,
            "role": "user",
            "created_at": datetime.utcnow()
        })

    # create session
    request.session["username"] = username
    request.session["email"] = email

    assistant_state.user_email = email

    return RedirectResponse(url="/dashboard")

@router.get("/logout")
def logout(request: Request):

    request.session.clear()

    # assistant_state.reset()

    return RedirectResponse(
        url="/",
        status_code=303
    )


@router.post("/admin/login")
def admin_login(data: AdminLogin, request: Request):

    #  Check allowed admin email
    if data.email not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized admin email"
        )

    # Find admin user in DB
    admin = user_auth_collection.find_one({
        "email": data.email,
        "role": "admin"
    })

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )

    # Verify password
    if not verify_password(data.password, admin["password"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    # Verify admin secret key
    if data.admin_key != ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin key"
        )

    # Create admin session
    request.session["username"] = admin["username"]
    request.session["email"] = admin["email"]
    request.session["role"] = "admin"

    # Redirect to admin dashboard
    return RedirectResponse(
        url="/admin/dashboard",
        status_code=303
    )

@router.post("/set-password")
def set_password(request: Request, data: dict):

    email = request.session.get("email")

    if not email:
        raise HTTPException(status_code=401, detail="Not logged in")

    password = data.get("password")

    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Weak password")

    hashed = hash_password(password)

    user_auth_collection.update_one(
        {"email": email},
        {
            "$set": {
                "password": hashed,
                "has_password": True
            }
        }
    )

    return {"message": "Password set"}


@router.post("/voice-auth")
def voice_auth(request: Request, data: dict):

    session = request.session

    # 🔥 Normalize input
    value = data.get("value")

    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""

    value = str(value or "").strip().lower()

    # 🔥 FORCE RESET (important)
    if value in ["new", "existing"]:
        session["voice_step"] = "entry"
        session.pop("voice_email", None)

    # 🔥 Init step
    if "voice_step" not in session:
        session["voice_step"] = "entry"

    step = session.get("voice_step")

    # ───────────── ENTRY ─────────────
    if step == "entry":

        if "existing" in value:
            session["voice_step"] = "ask_pin"
            return {
                "next": "ask_pin",
                "message": "Please say your 4 digit PIN"
            }

        elif "new" in value:
            session["voice_step"] = "start"
            return {
                "next": "ask_email",
                "message": "Please say your email username"
            }

        else:
            return {
                "next": "entry",
                "message": "Say new user or existing user"
            }

    # ───────────── EMAIL CAPTURE ─────────────
    if step == "start":

        email = normalize_email_username(value) + "@gmail.com"
        session["voice_email"] = email
        session["voice_step"] = "confirm_email"

        print("VOICE EMAIL:", email)

        return {
            "next": "confirm_email",
            "message": f"I heard {email}. Say yes to confirm or no to retry"
        }

    # ───────────── CONFIRM EMAIL ─────────────
    from app.utils.voice_utils import normalize_confirmation
    if step == "confirm_email":

        value = normalize_confirmation(value)

        if value == "yes":

            email = session.get("voice_email")

            if not email:
                session["voice_step"] = "entry"
                return {
                    "next": "entry",
                    "message": "Session lost. Start again"
                }

            user = user_auth_collection.find_one({"email": email})

            # Existing user → ask PIN
            if user and user.get("has_voice_pin"):
                session["voice_step"] = "ask_pin"
                return {
                    "next": "ask_pin",
                    "message": "Say your 4 digit PIN"
                }

            # New user → set PIN
            session["voice_step"] = "set_pin"
            return {
                "next": "set_pin",
                "message": "Please set your 4 digit PIN"
            }

        elif value == "no":
            session["voice_step"] = "start"
            return {
                "next": "retry_email",
                "message": "Okay, please say your email again"
            }

        else:
            return {
                "next": "confirm_email",
                "message": "Please say yes or no"
            }

    # ───────────── SET PIN (NEW USER) ─────────────
    if step == "set_pin":

        pin = normalize_pin(value)

        if not pin or len(pin) != 4:
            return {
                "error": "Invalid PIN format",
                "retry": True
            }

        email = session.get("voice_email")

        if not email:
            session["voice_step"] = "entry"
            return {
                "error": "Session expired. Start again",
                "retry": False
            }

        hashed_pin = hash_pin(pin)

        existing_user = user_auth_collection.find_one({"email": email})

        # ✅ update if exists
        if existing_user:
            user_auth_collection.update_one(
                {"email": email},
                {
                    "$set": {
                        "voice_pin": hashed_pin,
                        "has_voice_pin": True,
                        "provider": "voice"
                    }
                }
            )
        else:
            user_auth_collection.insert_one({
                "username": email.split("@")[0],
                "email": email,
                "password": None,
                "has_password": False,
                "voice_pin": hashed_pin,
                "has_voice_pin": True,
                "provider": "voice",
                "google_token": None,
                "role": "user",
                "created_at": datetime.utcnow()
            })

        # ✅ create session
        request.session["email"] = email
        request.session["username"] = email.split("@")[0]

        print("✅ SESSION SET (signup):", request.session)

        session["voice_step"] = "entry"

        return {"success": True}

    if step == "ask_pin":

        pin = normalize_pin(value)

        if not pin or len(pin) != 4:
            return {
                "error": "Invalid PIN format",
                "retry": True
            }

        #  Find user by PIN (scan)
        users = list(user_auth_collection.find({"has_voice_pin": True}))

        for user in users:
            try:
                if verify_pin(pin, user["voice_pin"]):

                    # LOGIN SUCCESS
                    request.session["email"] = user["email"]
                    request.session["username"] = user["email"].split("@")[0]

                    print(" LOGIN SUCCESS:", user["email"])

                    session["voice_step"] = "entry"

                    return {"success": True}

            except Exception as e:
                print("PIN VERIFY ERROR:", e)
                continue

        return {
            "error": "Invalid PIN",
            "retry": True
        }

    # ───────────── FALLBACK ─────────────
    session["voice_step"] = "entry"

    return {
        "next": "entry",
        "message": "Something went wrong. Start again"
    }


# RESET ROUTE
@router.post("/voice-auth/reset")
def reset_voice(request: Request):
    request.session["voice_step"] = "entry"
    request.session.pop("voice_email", None)
    return {"status": "reset"}


