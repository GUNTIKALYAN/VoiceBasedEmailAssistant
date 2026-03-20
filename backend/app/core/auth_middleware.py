from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from app.db import user_auth_collection


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        path = request.url.path

        public_paths = [
            "/", "/signup", "/admin/login",
            "/auth/login", "/auth/signup",
            "/auth/google/login", "/auth/google/callback", "/auth/logout",
            "/auth/set-password", "/auth/voice-auth", "/speak", "/static", "/stt-once", "/docs","/openapi.json","/redoc",
            "/whatsapp/webhook","/whatsapp/webhook/"
        ]

        # allow static
        if path.startswith("/static"):
            return await call_next(request)

        if path in public_paths:
            return await call_next(request)

        # detect API call
        is_api = request.headers.get("accept") == "application/json"

        def unauthorized():
            if is_api:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            return RedirectResponse(url="/")

        # session
        email = request.session.get("email")
        role = request.session.get("role")

        # admin routes
        if path.startswith("/admin"):
            if role != "admin":
                return unauthorized()
            return await call_next(request)

        # user routes
        if not email:
            return unauthorized()

        user = user_auth_collection.find_one({"email": email})

        if not user:
            return unauthorized()

        # force password setup
        if user.get("provider") != "voice" and not user.get("has_password") and path != "/set-password":
            return RedirectResponse(url="/set-password")
        
        return await call_next(request)