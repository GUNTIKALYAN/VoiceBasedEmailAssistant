from fastapi import APIRouter, Request, HTTPException
from app.db import user_auth_collection
from fastapi import Body

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats/users")
def get_total_users(request: Request):

    role = request.session.get("role")

    if role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    total_users = user_auth_collection.count_documents({})

    return {
        "total_users": total_users
    }


@router.get("/users")
def get_all_users(request: Request):

    role = request.session.get("role")

    if role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    users_cursor = user_auth_collection.find({}, {
        "_id": 0,
        "username": 1,
        "email": 1,
        "role": 1,
        "status": 1,
        "created_at": 1
    })

    users = list(users_cursor)

    return {
        "users": users
    }


@router.delete("/users/{email}")
def delete_user(email: str, request: Request):

    role = request.session.get("role")

    if role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Prevent deleting admins
    user = user_auth_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin")

    user_auth_collection.delete_one({"email": email})

    return {"message": "User deleted successfully"}


@router.patch("/users/status")
def update_user_status(request: Request, data: dict = Body(...)):

    role = request.session.get("role")

    if role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    email = data.get("email")
    status = data.get("status")

    if status not in ["active", "blocked"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    user = user_auth_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot modify admin")

    user_auth_collection.update_one(
        {"email": email},
        {"$set": {"status": status}}
    )

    return {"message": "User status updated"}

@router.post("/logout")
def admin_logout(request: Request):

    role = request.session.get("role")

    if role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    #  destroy session
    request.session.clear()

    return {"message": "Logged out successfully"}