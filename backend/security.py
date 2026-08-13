"""Auth primitives: password hashing, JWT, user dependencies, entitlement.

Session transport: the JWT lives in an httpOnly `ttn_session` cookie (XSS-safe —
scripts can never read it). The Authorization: Bearer header is still accepted as
a fallback so pre-cookie sessions keep working and can migrate via /auth/cookie-sync.
"""
from datetime import timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Depends, Cookie, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import JWT_SECRET, JWT_ALGO, JWT_EXPIRY_DAYS
from db import db
from utils import now_utc

security = HTTPBearer(auto_error=False)

SESSION_COOKIE = 'ttn_session'


def set_session_cookie(response: Response, token: str) -> None:
    """Attach the signed session JWT as a secure httpOnly cookie."""
    response.set_cookie(
        key=SESSION_COOKIE, value=token,
        httponly=True,           # invisible to JavaScript (XSS protection)
        secure=True,             # HTTPS only (browsers exempt localhost for dev)
        samesite='lax',          # CSRF posture: not sent on cross-site POSTs
        max_age=JWT_EXPIRY_DAYS * 24 * 3600,
        path='/',
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, path='/')


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def make_token(user_id: str) -> str:
    payload = {'sub': user_id, 'exp': now_utc() + timedelta(days=JWT_EXPIRY_DAYS), 'iat': now_utc()}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


async def user_from_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        return None
    user = await db.users.find_one({'id': payload.get('sub')})
    return user


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
                            ttn_session: Optional[str] = Cookie(default=None)):
    token = credentials.credentials if credentials else ttn_session
    if not token:
        return None
    return await user_from_token(token)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
                           ttn_session: Optional[str] = Cookie(default=None)):
    token = credentials.credentials if credentials else ttn_session
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    user = await user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    return user


async def get_admin_user(user=Depends(get_current_user)):
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='Admin access required')
    return user


async def is_entitled(user) -> bool:
    """Server-side premium entitlement check."""
    if not user:
        return False
    if user.get('role') == 'admin':
        return True
    sub = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    return sub is not None


async def get_premium_user(user=Depends(get_current_user)):
    if not await is_entitled(user):
        raise HTTPException(status_code=403, detail='The Lounge is for Premium members. Upgrade to join the conversation.')
    return user


def public_user(user, premium: bool):
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user.get('name', ''),
        'role': user.get('role', 'user'),
        'is_premium': premium,
        'created_at': user.get('created_at'),
        'current_streak': user.get('current_streak', 0),
        'longest_streak': user.get('longest_streak', 0),
        'last_read_date': user.get('last_read_date'),
        'streak_badges': sorted(set(int(b) for b in (user.get('streak_badges') or []))),
        'early_supporter': bool(user.get('early_supporter')),
    }
