from passlib.context import CryptContext
from fastapi import HTTPException


# Password Hashing Context
pwd_context = CryptContext(
    schemes=["bcrypt"],  
    deprecated="auto"
)

# Constants
MAX_BCRYPT_BYTES = 72
MIN_PASSWORD_LENGTH = 6

# Hash Password
def hash_password(password: str) -> str:
    """
    Hash user password using bcrypt.
    Includes:
    - Length validation
    - Encoding safety
    - Error handling
    """

    if not password:
        raise HTTPException(status_code=400, detail="Password cannot be empty")

    # Password length < 6 condition
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    # Convert to bytes length (bcrypt rule)
    pwd_bytes = password.encode("utf-8")

    
    if len(pwd_bytes) > MAX_BCRYPT_BYTES:
        raise HTTPException(status_code=400, detail="Password too long. Max 72 bytes allowed.")

    try:
        hashed_password = pwd_context.hash(password)
        return hashed_password

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password hashing failed: {str(e)}")


# Verify Password

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify plain password against stored hash.
    """

    if not password or not hashed:
        return False

    try:
        return pwd_context.verify(password, hashed)

    except Exception:
        return False
    

import bcrypt

def hash_pin(pin: str):
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()

def verify_pin(pin: str, hashed: str):
    return bcrypt.checkpw(pin.encode(), hashed.encode())