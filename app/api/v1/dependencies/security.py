import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, TypedDict, Dict
from fastapi import Response, Request
from uuid import UUID
from app.core.config import settings

JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
JWT_SECURE = settings.JWT_SECURE

class TokenPayload(TypedDict):
    sub: str
    iat: int
    exp: int
    role: str
    type: str

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(
    user_id: UUID,
    token_type: str,
    expires_delta: timedelta,
    role: str
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload = TokenPayload(
        sub=str(user_id),
        iat=int(now.timestamp()),
        exp=int(expire.timestamp()),
        type=token_type,
        role=role
    )
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_access_token(user_id:UUID, role: str) -> str:
    return create_token(
        user_id,
        "access",
        timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        role
    )

def create_refresh_token(user_id: UUID, role: str) -> str:
    return create_token(
        user_id,
        "refresh",
        timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        role
    )

def create_auth_tokens(user_id: UUID, role: str) -> dict:
    access_token = create_access_token(user_id, role)
    refresh_token= create_refresh_token(user_id, role)

    return {
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

def get_token_from_cookie(request: Request) -> Optional[str]:
    """
    Достает JWT токен из cookie.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    return token

def decode_token(token: str, expected_type: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        sub = payload.get("sub")
        if sub is None:
            return None
        
        return payload
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, TypeError):
        return None

def set_auth_cookies(response: Response, user_id: UUID):
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=JWT_SECURE,
        samesite="lax",  # кука не подставляется при отправке запроса с чужого сайта
        max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=JWT_SECURE,
        samesite="lax",
        max_age=JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )