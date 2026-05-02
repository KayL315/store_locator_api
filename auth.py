import os
import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
import bcrypt
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from database import get_session
from models import User


load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def hash_token(token: str) -> str:
    """
    Store only hash of refresh token in database.
    This is safer than storing raw refresh tokens.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_user_role_name(user: User) -> str:
    if not user.role:
        raise HTTPException(status_code=403, detail="User has no role assigned")

    return user.role.name


def create_access_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    role_name = get_user_role_name(user)

    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "role": role_name,
        "type": "access",
        "exp": expire,
        "jti": str(uuid4()),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    role_name = get_user_role_name(user)

    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "role": role_name,
        "type": "refresh",
        "exp": expire,
        "jti": str(uuid4()),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.exec(
        select(User).where(User.user_id == user_id)
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User is inactive")

    if not user.role:
        raise HTTPException(status_code=403, detail="User has no role assigned")

    return user


def require_permissions(required_permissions: list[str]):
    def dependency(current_user: User = Depends(get_current_user)):
        if not current_user.role:
            raise HTTPException(status_code=403, detail="User has no role assigned")

        user_permissions = {permission.name for permission in current_user.role.permissions}

        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(status_code=403, detail="Permission denied")

        return current_user

    return dependency