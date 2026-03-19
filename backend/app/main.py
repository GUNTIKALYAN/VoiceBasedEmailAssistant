# from fastapi import FastAPI, HTTPException, Request
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates
# from starlette.middleware.sessions import SessionMiddleware
# # from app.gmail.read import fetch_primary_emails_for_ui

# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Voice
# from app.voice.stt import speech_to_text
# from app.voice.edge_tts import speak
# from app.voice.wake_word import detect_wake_word
# from app.voice.voice_loop import run_voice_assistant

# # Commands
# from app.commands.command_parser import parse_command

# # Models
# from app.models.request_models import TextRequest, TextResponse

# # Auth router
# from app.auth.routes import router as auth_router
# from app.auth.dashboard_routes import router as dashboard_router


# # Gmail
# # from app.gmail.read import fetch_recent_primary_emails
# from app.services.gmail_service import fetch_recent_primary_emails


# # Assistant Exit
# from app.utils.assistant_control import request_exit 
# from app.utils.conversational_state import assistant_state


# app = FastAPI(title="Voice Email Assistant")

# # Session middleware
# app.add_middleware(
#     SessionMiddleware,
#     secret_key=os.getenv("SECRET_KEY")
# )
# # Template engine
# # Paths
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
# FRONTEND_PATH = os.path.join(PROJECT_ROOT, "frontend")
# VOICE_UI_PATH = os.path.join(FRONTEND_PATH, "voice-ui")
# AUTH_PATH = os.path.join(FRONTEND_PATH, "auth")

# # Templates
# templates = Jinja2Templates(directory=VOICE_UI_PATH)


# FRONTEND_PATH = os.path.join(PROJECT_ROOT, "frontend")
# VOICE_UI_PATH = os.path.join(FRONTEND_PATH, "voice-ui")
# AUTH_PATH = os.path.join(FRONTEND_PATH, "auth")
# ADMIN_PATH = os.path.join(FRONTEND_PATH, "admin")

# print("STATIC SERVED FROM:", FRONTEND_PATH)


# # Include routers
# app.include_router(auth_router)
# app.include_router(dashboard_router)

# # Static mount
# app.mount(
#     "/static",
#     StaticFiles(directory=FRONTEND_PATH),
#     name="static"
# )


# # LOGIN PAGE
# @app.get("/")
# def home():
#     return FileResponse(os.path.join(AUTH_PATH, "login.html"))


# # SIGNUP PAGE
# @app.get("/signup")
# def load_signup():
#     return FileResponse(os.path.join(AUTH_PATH, "signup.html"))


# @app.get("/admin/login")
# def load_admin_login():
#     return FileResponse(os.path.join(AUTH_PATH, "admin_login.html"))

# # VOICE LOOP
# @app.post("/voice-loop", response_model=TextResponse)
# def voice_to_voice():

#     result = run_voice_assistant()

#     if not result:
#         return {
#             "recognized_text": "",
#             "response": "Assistant ended"
#         }

#     return result


# # TEXT → SPEECH
# @app.post("/speak")
# def text_to_speech(data: TextRequest):

#     if not data.text.strip():
#         raise HTTPException(
#             status_code=400,
#             detail="Text cannot be empty"
#         )

#     speak(data.text)

#     return {
#         "status": "spoken",
#         "text": data.text
#     }


# @app.get("/emails/primary")
# def get_primary_emails(request: Request):

#     email = request.session.get("email")

#     if not email:
#         return {"error": []}

#     emails = fetch_recent_primary_emails(email, max_results=10)

#     return {"emails": emails}

# @app.post("/assistant-exit")
# def exit_assistant():
#     request_exit()
#     return {"status": "stop requested"}


# @app.get("/gmail/test")
# def gmail_test(request: Request):

#     email = request.session.get("email")

#     emails = fetch_recent_primary_emails(email)

#     return {"emails": emails}



from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import os
from dotenv import load_dotenv

load_dotenv()

# Voice
from app.voice.stt import speech_to_text
from app.voice.edge_tts import speak
from app.voice.wake_word import detect_wake_word
from app.voice.voice_loop import run_voice_assistant

# Commands
from app.commands.command_parser import parse_command

# Models
from app.models.request_models import TextRequest, TextResponse

# Auth routers
from app.auth.routes import router as auth_router
from app.auth.dashboard_routes import router as dashboard_router

# Gmail
from app.services.gmail_service import fetch_recent_primary_emails

# Assistant state + exit control
from app.utils.assistant_control import request_exit
from app.utils.conversational_state import assistant_state

# Admin Routes
from app.admin.routes import router as admin_router

from app.db import user_auth_collection

from app.core.auth_guard import require_user

from app.core.auth_middleware import AuthMiddleware

app = FastAPI(title="Voice Email Assistant")

# ── Middleware ─────────────────────────────────────────────────────────────
app.add_middleware(AuthMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY")
)

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
FRONTEND_PATH = os.path.join(PROJECT_ROOT, "frontend")
VOICE_UI_PATH = os.path.join(FRONTEND_PATH, "voice-ui")
AUTH_PATH = os.path.join(FRONTEND_PATH, "auth")
ADMIN_PATH = os.path.join(FRONTEND_PATH, "admin-ui")

print("STATIC SERVED FROM:", FRONTEND_PATH)

# ── Templates ──────────────────────────────────────────────────────────────
templates = Jinja2Templates(directory=VOICE_UI_PATH)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(admin_router)

# ── Static files ───────────────────────────────────────────────────────────
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_PATH),
    name="static"
)

# ── Pages ──────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return FileResponse(os.path.join(AUTH_PATH, "login.html"))


@app.get("/signup")
def load_signup():
    return FileResponse(os.path.join(AUTH_PATH, "signup.html"))


@app.get("/admin/login")
def load_admin_login():
    return FileResponse(os.path.join(AUTH_PATH, "admin_login.html"))


# ── Voice loop ─────────────────────────────────────────────────────────────

# @app.post("/voice-loop", response_model=TextResponse)
# def voice_to_voice(request: Request):
#     """
#     Start the voice assistant loop.
#     Reads the logged-in user's email from the session and injects it
#     into assistant_state so Gmail calls work correctly.
#     """

#     # ── Resolve the logged-in user ─────────────────────────────────────
#     # user_email = request.session.get("email")

#     # user = user_auth_collection.find_one({"email": user_email})
#     user = require_user(request)

#     if user.get("status") == "blocked":
#         raise HTTPException(
#             status_code=403,
#             detail="Your account has been blocked. Contact admin@voxmail.com"
#         )

#     assistant_state.user_email = user["email"]

#     print(f"[voice-loop] Starting assistant for user: {user['email']}")


#     if user and user.get("status") == "blocked":
#         raise HTTPException(
#             status_code=403,
#             detail="Your account has been blocked. Contact admin@voxmail.com"
#         )
    
#     assistant_state.user_email = user["email"]


#     # if not user_email:
#     #     raise HTTPException(
#     #         status_code=401,
#     #         detail="Not logged in. Please sign in first."
#     #     )



#     # # Inject into shared assistant state so command_parser can use it
#     # assistant_state.user_email = user_email

#     print(f"[voice-loop] Starting assistant for user: {user['email']}")

#     # ── Run the blocking voice loop ────────────────────────────────────
#     result = run_voice_assistant()

#     if not result:
#         return {
#             "recognized_text": "",
#             "response": "Assistant ended"
#         }

#     return result

@app.post("/voice-loop")
def voice_to_voice(request: Request):

    # user = require_user(request)
    email = request.session.get("email")
    if not email:
        raise HTTPException(
            status_code=401,
            detail="Not logged in"
        )
    
    user = user_auth_collection.find_one({"email": email})

    if user.get("status") == "blocked":
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked. Contact admin@voxmail.com"
        )

    assistant_state.user_email = user["email"]
    assistant_state.username = user["username"]

    print(f"[voice-loop] Starting assistant for user: {user['email']}")

    result = run_voice_assistant()

    if not result:
        return {
            "recognized_text": "",
            "response": "Assistant ended"
        }

    return result

from app.voice.stt import speech_to_text

# @app.post("/stt-once")
# def stt_once():
#     print("SST triggered")

#     result = speech_to_text()

#     if isinstance(result,tuple):
#         text = result[0]

#     print("Recognized:", text)



#     if not text:
#         return {
#             "recognized_text": "",
#             "error": "No speech detected"
#         }

#     return {
#         "recognized_text": text
#     }

# @app.post("/stt-once")
# def stt_once():

#     print("SST triggered")

#     text, lang = speech_to_text()

#     print("Recognized:", text)

#     if not text:
#         return {
#             "recognized_text": "",
#             "response": "No speech detected"
#         }
#     # ─────────────────────────────────────────
#     # STEP 1: NEW USER TRIGGER
#     # ─────────────────────────────────────────
#     if assistant_state.user_email is None:

#         if "new user" in text:

#             assistant_state.auth_mode = "new_user"
#             assistant_state.awaiting_email = True

#             return {
#                 "recognized_text": text,
#                 "response": "Please tell me your registered email."
#             }
#     # ─────────────────────────────────────────
#     # 2. EMAIL CAPTURE (HIGHEST PRIORITY)
#     # ─────────────────────────────────────────
#     from app.utils.voice_utils import normalize_email_full, normalize_pin
#     if getattr(assistant_state, "awaiting_email", False):

#         email = normalize_email_full(text)

#         user = user_auth_collection.find_one({"email": email})

#         if not user:
#             return {
#                 "recognized_text": text,
#                 "response": "User not found. Please login using Google first."
#             }

#         assistant_state.user_email = email
#         assistant_state.username = user.get("username")
#         assistant_state.awaiting_email = False

#         # 🔥 CHECK PIN EXISTS
#         if user.get("pin"):
#             assistant_state.awaiting_pin = True

#             return {
#                 "recognized_text": text,
#                 "response": "Please say your 4 digit PIN."
#             }

#         else:
#             assistant_state.awaiting_pin_creation = True

#             return {
#                 "recognized_text": text,
#                 "response": "You don't have a PIN. Please create a 4 digit PIN."
#             }

#     # ─────────────────────────────────────────
#     # 2. PIN CREATION
#     # ─────────────────────────────────────────
#     if getattr(assistant_state, "awaiting_pin_creation", False):

#         pin = normalize_pin(text)

#         if len(pin) != 4:
#             return {
#                 "recognized_text": text,
#                 "response": "PIN must be 4 digits. Say again."
#             }

#         user_auth_collection.insert_one({
#             "email": assistant_state.user_email,
#             "pin": pin,
#             "provider": "voice",
#             "username": assistant_state.user_email.split("@")[0]
#         })

#         assistant_state.awaiting_pin_creation = False

#         return {
#             "recognized_text": text,
#             "response": "Account created successfully. You can start using the assistant."
#         }

#     # ─────────────────────────────────────────
#     # 3. LOGIN / SIGNUP TRIGGER
#     # ─────────────────────────────────────────
#     if assistant_state.user_email is None:

#         if "new user" in text:

#             assistant_state.auth_mode = "signup"
#             assistant_state.awaiting_email = True

#             return {
#                 "recognized_text": text,
#                 "response": "Please tell me your email address."
#             }

#         elif "login" in text or "existing user" in text:

#             assistant_state.auth_mode = "login"
#             assistant_state.awaiting_email = True

#             return {
#                 "recognized_text": text,
#                 "response": "Please say your registered email."
#             }

#         else:
#             return {
#                 "recognized_text": text,
#                 "response": "Say new user or login."
#             }

#     # ─────────────────────────────────────────
#     # 4. NORMAL COMMAND FLOW
#     # ─────────────────────────────────────────
#     response = parse_command(text)

#     return {
#         "recognized_text": text,
#         "response": response
#     }
    

@app.post("/stt-once")
def stt_once(request: Request):

    print("SST triggered")

    text, lang = speech_to_text()

    print("Recognized:", text)

    if not text:
        return {
            "recognized_text": "",
            "response": "No speech detected"
        }

    from app.utils.voice_utils import (
        normalize_email_full,
        normalize_pin,
        normalize_confirmation
    )

    # ─────────────────────────────────────────
    # STEP 1: TRIGGER NEW USER FLOW
    # ─────────────────────────────────────────
    if assistant_state.user_email is None:

        if "new user" in text:

            assistant_state.auth_mode = "new_user"
            assistant_state.awaiting_email = True

            return {
                "recognized_text": text,
                "response": "Please tell me your registered email."
            }

        return {
            "recognized_text": text,
            "response": "Please say new user to continue."
        }

    # ─────────────────────────────────────────
    # STEP 2: EMAIL CAPTURE + DB CHECK
    # ─────────────────────────────────────────
    if getattr(assistant_state, "awaiting_email", False):

        email = normalize_email_full(text)

        user = user_auth_collection.find_one({"email": email})

        if not user:
            return {
                "recognized_text": text,
                "response": "User not found. Please login using Google first."
            }

        assistant_state.user_email = email
        assistant_state.username = user.get("username")
        assistant_state.awaiting_email = False

        # PIN exists → go to login
        if user.get("pin"):
            assistant_state.awaiting_pin = True

            return {
                "recognized_text": text,
                "response": "Please say your 4 digit PIN."
            }

        # No PIN → create PIN
        assistant_state.awaiting_pin_creation = True

        return {
            "recognized_text": text,
            "response": "You don't have a PIN. Please create a 4 digit PIN."
        }

    # ─────────────────────────────────────────
    # STEP 3.1: PIN CAPTURE
    # ─────────────────────────────────────────
    if getattr(assistant_state, "awaiting_pin_creation", False):

        pin = normalize_pin(text)

        if len(pin) != 4:
            return {
                "recognized_text": text,
                "response": "PIN must be 4 digits. Say again."
            }

        assistant_state.temp_pin = pin
        assistant_state.awaiting_pin_creation = False
        assistant_state.awaiting_pin_confirmation = True

        return {
            "recognized_text": text,
            "response": f"You said {pin}. Is this correct?"
        }

    # ─────────────────────────────────────────
    # STEP 3.2: PIN CONFIRMATION
    # ─────────────────────────────────────────
    if getattr(assistant_state, "awaiting_pin_confirmation", False):

        decision = normalize_confirmation(text)

        if decision == "no":

            assistant_state.awaiting_pin_creation = True
            assistant_state.awaiting_pin_confirmation = False

            return {
                "recognized_text": text,
                "response": "Okay, please say the PIN again."
            }

        elif decision == "yes":

            user_auth_collection.update_one(
                {"email": assistant_state.user_email},
                {"$set": {"pin": assistant_state.temp_pin}}
            )

            assistant_state.awaiting_pin_confirmation = False
            assistant_state.awaiting_pin = True

            return {
                "recognized_text": text,
                "response": "PIN saved successfully. Now say your PIN to login."
            }

        return {
            "recognized_text": text,
            "response": "Please say yes or no."
        }

    # ─────────────────────────────────────────
    # STEP 4: PIN LOGIN + SESSION + REDIRECT
    # ─────────────────────────────────────────
    if getattr(assistant_state, "awaiting_pin", False):

        pin = normalize_pin(text)

        user = user_auth_collection.find_one({
            "email": assistant_state.user_email
        })

        if user and user.get("pin") == pin:

            assistant_state.awaiting_pin = False

            # 🔥 SESSION SET (CRITICAL)
            request.session["email"] = assistant_state.user_email

            return {
                "recognized_text": text,
                "response": "Login successful. Redirecting to dashboard.",
                "redirect": "/dashboard"
            }

        else:
            return {
                "recognized_text": text,
                "response": "Incorrect PIN. Try again."
            }

    # ─────────────────────────────────────────
    # STEP 5: NORMAL COMMAND FLOW
    # ─────────────────────────────────────────
    response = parse_command(text)

    return {
        "recognized_text": text,
        "response": response
    }

# ── Text → Speech ──────────────────────────────────────────────────────────

@app.post("/speak")
def text_to_speech(data: TextRequest):

    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    speak(data.text)

    return {"status": "spoken", "text": data.text}


# ── Email endpoints ────────────────────────────────────────────────────────

@app.get("/emails/primary")
def get_primary_emails(request: Request):

    email = request.session.get("email")

    # email = request.session.get("email")

    if not email:
        return HTTPException(status_code=401, detail="Unauthorized")

    emails = fetch_recent_primary_emails(email, max_results=10)

    return {"emails": emails}


@app.get("/gmail/test")
def gmail_test(request: Request):

    # user = require_user(request)

    email = request.session.get("email")

    # if not email:
    #     return {"error": "Not logged in", "emails": []}

    emails = fetch_recent_primary_emails(email)

    return {"emails": emails}


# ── Assistant control ──────────────────────────────────────────────────────

@app.post("/assistant-exit")
def exit_assistant():
    request_exit()
    return {"status": "stop requested"}



@app.get("/admin/dashboard")
def admin_dashboard(request: Request):

    role = request.session.get("role")

    if role != "admin":
        return RedirectResponse(url="/admin/login")

    return FileResponse(
        os.path.join(ADMIN_PATH, "admin.html")
    )

@app.get("/set-password")
def load_set_password():
    return FileResponse(os.path.join(AUTH_PATH, "set_password.html"))

@app.get("/dashboard")
def dashboard(request: Request):

    email = request.session.get("email")

    if not email:
        return RedirectResponse(url="/")

    user = user_auth_collection.find_one({"email": email})

    if not user:
        return RedirectResponse(url="/")
    
    #  Force password setup
    if user["provider"] != "voice" and not user.get("has_password"):
        return RedirectResponse(url="/set-password")
    
    print("SESSION IN DASHBOARD:", request.session)

    return templates.TemplateResponse("index.html", {"request": request})

for route in app.routes:
    print(route.path)

from app.voice.voice_loop import LIVE_LOGS

@app.get("/logs")
def get_logs():

    logs = list(LIVE_LOGS)

    # 🔥 clear after sending (important)
    LIVE_LOGS.clear()

    return {
        "logs": logs
    }