"""Auth routes: register, login, magic links, password reset."""
import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends

from config import FRONTEND_URL, logger
from db import db
from utils import now_utc, iso
from security import (hash_password, verify_password, make_token, get_current_user,
                      is_entitled, public_user)
from schemas import (RegisterIn, LoginIn, MagicRequestIn, MagicVerifyIn,
                     PasswordResetRequestIn, PasswordResetConfirmIn)
from services.emailer import log_email

router = APIRouter(prefix='/api')


@router.post('/auth/register')
async def register(body: RegisterIn):
    existing = await db.users.find_one({'email': body.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail='An account with this email already exists')
    user = {
        'id': str(uuid.uuid4()), 'email': body.email.lower(), 'name': body.name,
        'password_hash': hash_password(body.password), 'role': 'user',
        'created_at': iso(now_utc()),
    }
    await db.users.insert_one(dict(user))
    token = make_token(user['id'])
    return {'token': token, 'user': public_user(user, False)}


@router.post('/auth/login')
async def login(body: LoginIn):
    user = await db.users.find_one({'email': body.email.lower()})
    if not user or not user.get('password_hash') or not verify_password(body.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    premium = await is_entitled(user)
    return {'token': make_token(user['id']), 'user': public_user(user, premium)}


@router.post('/auth/magic-link/request')
async def magic_request(body: MagicRequestIn):
    email = body.email.lower()
    # rate limit: max 5 tokens per email per hour
    hour_ago = iso(now_utc() - timedelta(hours=1))
    count = await db.magic_tokens.count_documents({'email': email, 'created_at': {'$gte': hour_ago}})
    if count >= 5:
        raise HTTPException(status_code=429, detail='Too many magic link requests. Try again later.')
    token = str(uuid.uuid4())
    await db.magic_tokens.insert_one({
        'id': str(uuid.uuid4()), 'email': email, 'token': token, 'used': False,
        'expires_at': iso(now_utc() + timedelta(minutes=15)), 'created_at': iso(now_utc()),
    })
    link = f"{FRONTEND_URL}/auth/magic?token={token}"
    await log_email(email, 'Your magic sign-in link — The Trading Narrative',
                    f'Click to sign in: {link} (expires in 15 minutes)', 'magic_link')
    logger.info(f'[MAGIC LINK - MOCKED EMAIL] {email} -> {link}')
    # MOCKED: since no email provider configured, return the link so UI can display it (dev mode)
    return {'ok': True, 'dev_mode': True, 'magic_link': link,
            'message': 'Email sending is mocked — use the link below to sign in.'}


@router.post('/auth/magic-link/verify')
async def magic_verify(body: MagicVerifyIn):
    rec = await db.magic_tokens.find_one({'token': body.token})
    if not rec or rec.get('used'):
        raise HTTPException(status_code=400, detail='Invalid or already used magic link')
    if rec['expires_at'] < iso(now_utc()):
        raise HTTPException(status_code=400, detail='Magic link has expired')
    await db.magic_tokens.update_one({'token': body.token}, {'$set': {'used': True}})
    user = await db.users.find_one({'email': rec['email']})
    if not user:
        user = {
            'id': str(uuid.uuid4()), 'email': rec['email'],
            'name': rec['email'].split('@')[0].replace('.', ' ').title(),
            'password_hash': None, 'role': 'user', 'created_at': iso(now_utc()),
        }
        await db.users.insert_one(dict(user))
    premium = await is_entitled(user)
    return {'token': make_token(user['id']), 'user': public_user(user, premium)}


@router.get('/auth/me')
async def me(user=Depends(get_current_user)):
    premium = await is_entitled(user)
    return {'user': public_user(user, premium)}


@router.post('/auth/password-reset/request')
async def password_reset_request(body: PasswordResetRequestIn):
    email = body.email.lower()
    # rate limit: max 5 requests per email per hour
    hour_ago = iso(now_utc() - timedelta(hours=1))
    count = await db.password_reset_tokens.count_documents({'email': email, 'created_at': {'$gte': hour_ago}})
    if count >= 5:
        raise HTTPException(status_code=429, detail='Too many reset requests. Try again later.')
    user = await db.users.find_one({'email': email})
    if not user:
        # do not reveal whether an account exists
        return {'ok': True, 'dev_mode': True, 'reset_link': None,
                'message': 'If an account exists for that email, a reset link has been generated.'}
    token = str(uuid.uuid4())
    await db.password_reset_tokens.insert_one({
        'id': str(uuid.uuid4()), 'email': email, 'token': token, 'used': False,
        'expires_at': iso(now_utc() + timedelta(minutes=15)), 'created_at': iso(now_utc()),
    })
    link = f'{FRONTEND_URL}/auth/reset?token={token}'
    await log_email(email, 'Reset your password — The Trading Narrative',
                    f'Reset your password here: {link} (expires in 15 minutes)', 'password_reset')
    logger.info(f'[PASSWORD RESET - MOCKED EMAIL] {email} -> {link}')
    # MOCKED: no email provider configured, return the link so the UI can display it (dev mode)
    return {'ok': True, 'dev_mode': True, 'reset_link': link,
            'message': 'Email sending is mocked — use the link below to reset your password.'}


@router.post('/auth/password-reset/confirm')
async def password_reset_confirm(body: PasswordResetConfirmIn):
    rec = await db.password_reset_tokens.find_one({'token': body.token})
    if not rec or rec.get('used'):
        raise HTTPException(status_code=400, detail='Invalid or already used reset link')
    if rec['expires_at'] < iso(now_utc()):
        raise HTTPException(status_code=400, detail='Reset link has expired')
    user = await db.users.find_one({'email': rec['email']})
    if not user:
        raise HTTPException(status_code=400, detail='Account no longer exists')
    await db.password_reset_tokens.update_one({'token': body.token}, {'$set': {'used': True}})
    await db.users.update_one({'id': user['id']}, {'$set': {'password_hash': hash_password(body.password)}})
    premium = await is_entitled(user)
    return {'ok': True, 'token': make_token(user['id']), 'user': public_user(user, premium),
            'message': 'Password updated. You are now signed in.'}
