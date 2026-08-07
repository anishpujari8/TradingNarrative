"""Auth primitives: password hashing, JWT, user dependencies, entitlement."""
from datetime import timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import JWT_SECRET, JWT_ALGO, JWT_EXPIRY_DAYS
from db import db
from utils import now_utc

security = HTTPBearer(auto_error=False)


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


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        return None
    return await user_from_token(credentials.credentials)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail='Not authenticated')
    user = await user_from_token(credentials.credentials)
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
    }
