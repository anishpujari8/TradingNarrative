"""Auth routes: register, login, magic links, password reset."""
import uuid
from datetime import timedelta, date

from fastapi import APIRouter, HTTPException, Depends, Response

from config import FRONTEND_URL, EARLY_SUPPORTER_LIMIT, logger
from db import db
from utils import now_utc, iso
from security import (hash_password, verify_password, make_token, get_current_user,
                      is_entitled, public_user, set_session_cookie, clear_session_cookie)
from schemas import (RegisterIn, LoginIn, MagicRequestIn, MagicVerifyIn,
                     PasswordResetRequestIn, PasswordResetConfirmIn, StreakReadIn)
from services.emailer import log_email, notify_admin_new_subscriber

router = APIRouter(prefix='/api')


async def _is_early_supporter_slot_open() -> bool:
    """Launch promo: the first EARLY_SUPPORTER_LIMIT registered readers get early-supporter
    perks (the first 5 published essays are free for them)."""
    return await db.users.count_documents({'early_supporter': True}) < EARLY_SUPPORTER_LIMIT


@router.post('/auth/register')
async def register(body: RegisterIn, response: Response):
    existing = await db.users.find_one({'email': body.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail='An account with this email already exists')
    user = {
        'id': str(uuid.uuid4()), 'email': body.email.lower(), 'name': body.name,
        'password_hash': hash_password(body.password), 'role': 'user',
        'early_supporter': await _is_early_supporter_slot_open(),
        'created_at': iso(now_utc()),
    }
    await db.users.insert_one(dict(user))
    # session travels in an httpOnly cookie only — never exposed to page scripts
    set_session_cookie(response, make_token(user['id']))
    # Admin alert: new free account (branded, non-blocking)
    await notify_admin_new_subscriber(body.name, user['email'], 'Free account')
    return {'user': public_user(user, False)}


@router.post('/auth/login')
async def login(body: LoginIn, response: Response):
    user = await db.users.find_one({'email': body.email.lower()})
    if not user or not user.get('password_hash') or not verify_password(body.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    premium = await is_entitled(user)
    set_session_cookie(response, make_token(user['id']))
    return {'user': public_user(user, premium)}


@router.post('/auth/logout')
async def logout(response: Response):
    """Clear the httpOnly session cookie (script code cannot, by design)."""
    clear_session_cookie(response)
    return {'ok': True}


@router.post('/auth/cookie-sync')
async def cookie_sync(response: Response, user=Depends(get_current_user)):
    """One-time migration: exchange a legacy Bearer token (old localStorage sessions)
    for the httpOnly session cookie, so the frontend can drop the stored token."""
    set_session_cookie(response, make_token(user['id']))
    return {'ok': True}


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
    await log_email(email, 'Your magic sign-in link · The Trading Narrative',
                    f'Click to sign in: {link} (expires in 15 minutes)', 'magic_link')
    logger.info(f'[MAGIC LINK - MOCKED EMAIL] {email} -> {link}')
    # MOCKED: since no email provider configured, return the link so UI can display it (dev mode)
    return {'ok': True, 'dev_mode': True, 'magic_link': link,
            'message': 'Email sending is mocked, use the link below to sign in.'}


@router.post('/auth/magic-link/verify')
async def magic_verify(body: MagicVerifyIn, response: Response):
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
            'password_hash': None, 'role': 'user',
            'early_supporter': await _is_early_supporter_slot_open(),
            'created_at': iso(now_utc()),
        }
        await db.users.insert_one(dict(user))
    premium = await is_entitled(user)
    set_session_cookie(response, make_token(user['id']))
    return {'user': public_user(user, premium)}


@router.get('/auth/me')
async def me(user=Depends(get_current_user)):
    premium = await is_entitled(user)
    return {'user': public_user(user, premium)}


@router.get('/early-supporters')
async def early_supporters_status():
    """Public promo counter: how many of the first-50 early supporter spots remain."""
    taken = await db.users.count_documents({'early_supporter': True})
    left = max(0, EARLY_SUPPORTER_LIMIT - taken)
    return {'limit': EARLY_SUPPORTER_LIMIT, 'taken': min(taken, EARLY_SUPPORTER_LIMIT), 'left': left}


STREAK_MILESTONES = (7, 30, 100)


@router.post('/users/streak/read')
async def record_streak_read(body: StreakReadIn, user=Depends(get_current_user)):
    """Record a reading day for the signed-in user and update their streak.

    Streak rules (based on the reader's LOCAL calendar day, derived from the
    client tz offset): same day = no change; consecutive day = +1; gap = reset to 1.
    Idempotent for multiple reads on the same day.
    """
    # clamp offset to valid range (-14h .. +14h) to avoid abuse
    offset = max(-840, min(840, int(body.tz_offset_minutes or 0)))
    # JS getTimezoneOffset(): positive means local is BEHIND UTC -> subtract
    local_now = now_utc() - timedelta(minutes=offset)
    today = local_now.date()

    current = int(user.get('current_streak') or 0)
    longest = int(user.get('longest_streak') or 0)
    last_str = user.get('last_read_date')
    extended = False

    last_day = None
    if last_str:
        try:
            last_day = date.fromisoformat(last_str)
        except (ValueError, TypeError):
            last_day = None

    if last_day == today:
        pass  # already counted today
    elif last_day == today - timedelta(days=1):
        current += 1
        extended = True
    else:
        current = 1
        extended = True
    longest = max(longest, current)

    # milestone celebration + permanent badges (7 / 30 / 100 consecutive days)
    badges = sorted(set(int(b) for b in (user.get('streak_badges') or [])))
    milestone = current if (extended and current in STREAK_MILESTONES) else None
    new_badges = [m for m in STREAK_MILESTONES if longest >= m and m not in badges]
    if new_badges:
        badges = sorted(badges + new_badges)

    if extended:
        await db.users.update_one({'id': user['id']}, {'$set': {
            'current_streak': current, 'longest_streak': longest,
            'last_read_date': today.isoformat(),
            'streak_badges': badges,
        }})
    return {'ok': True, 'extended': extended,
            'current_streak': current, 'longest_streak': longest,
            'milestone': milestone, 'streak_badges': badges,
            'last_read_date': today.isoformat()}


def _reset_email_html(link: str) -> str:
    """Branded password reset email (teal identity, multipart-friendly)."""
    return f'''
<div style="max-width:560px;margin:0 auto;font-family:Georgia,serif;background:#faf8f3;border:1px solid #e2ddd2;border-radius:12px;overflow:hidden">
  <div style="background:#161a2e;padding:24px;text-align:center">
    <p style="color:#1c8570;font-family:monospace;font-size:11px;letter-spacing:3px;text-transform:uppercase;margin:0 0 6px">The Trading Narrative</p>
    <p style="color:#f2ede7;font-size:19px;margin:0;font-weight:600">Reset your password</p>
  </div>
  <div style="padding:26px 28px">
    <p style="font-size:15px;color:#2b2b2b;line-height:1.65;margin:0 0 18px">
      Someone (hopefully you) asked to reset the password for this account.
      Click the button below to choose a new password. This link expires in <strong>30 minutes</strong>.
    </p>
    <a href="{link}" style="display:inline-block;background:#1c8570;color:#ffffff;text-decoration:none;font-family:sans-serif;font-size:14px;font-weight:600;padding:12px 24px;border-radius:8px">Choose a new password</a>
    <p style="font-size:13px;color:#6b6b6b;line-height:1.6;margin:20px 0 0">
      If the button does not work, copy this link into your browser:<br>
      <a href="{link}" style="color:#1c8570;word-break:break-all">{link}</a>
    </p>
  </div>
  <div style="padding:14px 28px;border-top:1px solid #e2ddd2">
    <p style="font-size:12px;color:#8a8578;font-family:sans-serif;margin:0">
      If you did not request this, you can safely ignore this email, your password will not change.
    </p>
  </div>
</div>'''


@router.post('/auth/password-reset/request')
async def password_reset_request(body: PasswordResetRequestIn):
    email = body.email.lower()
    generic = {'ok': True,
               'message': 'If an account exists for that email, a reset link is on its way. '
                          'Check your inbox (and the spam folder), it expires in 30 minutes.'}
    # rate limit: max 5 requests per email per hour
    hour_ago = iso(now_utc() - timedelta(hours=1))
    count = await db.password_reset_tokens.count_documents({'email': email, 'created_at': {'$gte': hour_ago}})
    if count >= 5:
        raise HTTPException(status_code=429, detail='Too many reset requests. Try again later.')
    user = await db.users.find_one({'email': email})
    if not user:
        # do not reveal whether an account exists
        return generic
    token = str(uuid.uuid4())
    await db.password_reset_tokens.insert_one({
        'id': str(uuid.uuid4()), 'email': email, 'token': token, 'used': False,
        'expires_at': iso(now_utc() + timedelta(minutes=30)), 'created_at': iso(now_utc()),
    })
    link = f'{FRONTEND_URL}/auth/reset?token={token}'
    await log_email(email, 'Reset your password · The Trading Narrative',
                    (f'Someone (hopefully you) asked to reset your password on The Trading Narrative.\n\n'
                     f'Choose a new password here (expires in 30 minutes):\n{link}\n\n'
                     f'If you did not request this, ignore this email and your password will not change.'),
                    'password_reset', html=_reset_email_html(link))
    logger.info(f'[PASSWORD RESET] email sent to {email}')
    # SECURITY: never return the reset link in the API response, email delivery only.
    return generic


@router.post('/auth/password-reset/confirm')
async def password_reset_confirm(body: PasswordResetConfirmIn, response: Response):
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
    set_session_cookie(response, make_token(user['id']))
    return {'ok': True, 'user': public_user(user, premium),
            'message': 'Password updated. You are now signed in.'}
