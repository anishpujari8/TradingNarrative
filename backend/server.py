from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
import logging
import bcrypt
import jwt
import uuid
import math
import random
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from seed_data import SAMPLE_POSTS, AUTHOR  # noqa: E402
import stripe as stripe_sdk  # noqa: E402
from emergentintegrations.payments.stripe.checkout import (  # noqa: E402
    StripeCheckout, CheckoutSessionRequest,
)

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret')
JWT_ALGO = 'HS256'
JWT_EXPIRY_DAYS = 30
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
MOCK_BILLING = os.environ.get('MOCK_BILLING', 'true').lower() == 'true'
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')
# Shared Emergent test key: one-time timed passes (proxy blocks Subscription cancel API).
# User's own key: true auto-renewing subscriptions + Stripe-side cancellation.
IS_SHARED_STRIPE_KEY = 'sk_test_emergent' in STRIPE_API_KEY
AUTO_RENEW = not IS_SHARED_STRIPE_KEY


RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


RAZORPAY_SUBS_ENABLED = False  # probed at startup — True when the account has Subscriptions (UPI Autopay) enabled
RAZORPAY_LAST_PROBE = 0.0  # unix ts of last capability probe (throttles live re-checks)


def razorpay_client():
    import razorpay
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


async def probe_razorpay_subscriptions():
    global RAZORPAY_SUBS_ENABLED
    if not RAZORPAY_ENABLED:
        RAZORPAY_SUBS_ENABLED = False
        return
    try:
        import asyncio
        await asyncio.to_thread(lambda: razorpay_client().subscription.all({'count': 1}))
        RAZORPAY_SUBS_ENABLED = True
        logger.info('Razorpay Subscriptions (UPI Autopay) ENABLED on this account')
    except Exception:
        RAZORPAY_SUBS_ENABLED = False
        logger.info('Razorpay Subscriptions not enabled on this account — using one-time INR passes')


async def maybe_reprobe_razorpay(force: bool = False):
    """Live re-check of the Subscriptions capability (max once per 10 min) so
    UPI Autopay switches on automatically once enabled on the Razorpay dashboard,
    without needing a backend restart."""
    global RAZORPAY_LAST_PROBE
    import time as _time
    if not RAZORPAY_ENABLED or RAZORPAY_SUBS_ENABLED:
        return
    if not force and _time.time() - RAZORPAY_LAST_PROBE < 600:
        return
    RAZORPAY_LAST_PROBE = _time.time()
    await probe_razorpay_subscriptions()


async def get_or_create_razorpay_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    key = f'razorpay_plan_{plan_id}'
    stored = await db.config.find_one({'key': key})
    if stored:
        return stored['value']
    import asyncio
    rz_plan = await asyncio.to_thread(lambda: razorpay_client().plan.create({
        'period': 'monthly' if plan_id == 'monthly' else 'yearly', 'interval': 1,
        'item': {'name': f"The Trading Narrative Premium — {plan['label']} (INR)",
                 'amount': int(round(plan['amount_inr'] * 100)), 'currency': 'INR'},
    }))
    await db.config.update_one({'key': key}, {'$set': {'value': rz_plan['id']}}, upsert=True)
    return rz_plan['id']


def configure_stripe_sdk():
    stripe_sdk.api_key = STRIPE_API_KEY
    if IS_SHARED_STRIPE_KEY:
        stripe_sdk.api_base = 'https://integrations.emergentagent.com/stripe'
    return stripe_sdk


PLANS = {
    'monthly': {'id': 'monthly', 'label': 'Monthly', 'amount': 8.00, 'currency': 'usd',
                'amount_inr': 199.00, 'interval': 'month', 'period_days': 30},
    'annual': {'id': 'annual', 'label': 'Annual', 'amount': 80.00, 'currency': 'usd',
               'amount_inr': 1999.00, 'interval': 'year', 'period_days': 365},
}

CATEGORIES = {
    'tech-business': 'Tech & AI',
    'finance': 'Business & Finance',
    'lifestyle': 'Personal Growth',
    'travel': 'Travel',
}

PREVIEW_BLOCKS = 3  # paragraphs shown to non-premium users on premium posts

# ---------------------- traffic source classification ----------------------

TRAFFIC_SOURCE_MAP = {
    'linkedin': 'LinkedIn', 'lnkd.in': 'LinkedIn',
    'instagram': 'Instagram', 'ig.me': 'Instagram', 'l.instagram': 'Instagram',
    't.co': 'X (Twitter)', 'twitter': 'X (Twitter)', 'x.com': 'X (Twitter)',
    'facebook': 'Facebook', 'fb.me': 'Facebook', 'l.facebook': 'Facebook', 'm.facebook': 'Facebook',
    'google': 'Google', 'bing': 'Bing', 'duckduckgo': 'DuckDuckGo', 'yahoo': 'Yahoo',
    'youtube': 'YouTube', 'youtu.be': 'YouTube',
    'reddit': 'Reddit', 'out.reddit': 'Reddit',
    'whatsapp': 'WhatsApp', 'wa.me': 'WhatsApp',
    'telegram': 'Telegram', 't.me': 'Telegram',
    'substack': 'Substack', 'medium': 'Medium',
    'news.ycombinator': 'Hacker News', 'threads.net': 'Threads',
    'pinterest': 'Pinterest', 'quora': 'Quora', 'discord': 'Discord',
    'newsletter': 'Newsletter', 'email': 'Newsletter', 'mail': 'Newsletter',
}


def classify_traffic_source(referrer: str = '', utm_source: str = ''):
    """Return (source_label, referrer_host). source_label is None for internal navigation."""
    from urllib.parse import urlparse
    if utm_source:
        u = utm_source.strip().lower()
        for key, label in TRAFFIC_SOURCE_MAP.items():
            if key in u:
                return label, (urlparse(referrer).netloc.lower() if referrer else '')
        return utm_source.strip().title(), (urlparse(referrer).netloc.lower() if referrer else '')
    if not referrer:
        return 'Direct', ''
    host = urlparse(referrer).netloc.lower()
    if not host:
        return 'Direct', ''
    own_host = urlparse(FRONTEND_URL).netloc.lower() if FRONTEND_URL else ''
    if own_host and host == own_host:
        return None, host  # internal navigation — not a traffic source
    for key, label in TRAFFIC_SOURCE_MAP.items():
        if key in host:
            return label, host
    return 'Other', host


app = FastAPI(title='The Trading Narrative API')
api_router = APIRouter(prefix='/api')
security = HTTPBearer(auto_error=False)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ttn')


# ---------------------- helpers ----------------------

def now_utc():
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def clean(doc):
    """Strip Mongo _id and return JSON-safe doc."""
    if doc is None:
        return None
    doc.pop('_id', None)
    for k, v in list(doc.items()):
        if isinstance(v, datetime):
            doc[k] = iso(v)
    return doc


def slugify(title: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return s[:80] or str(uuid.uuid4())[:8]


def read_time(blocks: List[str]) -> int:
    words = sum(len(b.split()) for b in blocks)
    return max(1, math.ceil(words / 200))


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


def public_user(user, premium: bool):
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user.get('name', ''),
        'role': user.get('role', 'user'),
        'is_premium': premium,
        'created_at': user.get('created_at'),
    }


def post_summary(p):
    return {
        'id': p['id'], 'slug': p['slug'], 'title': p['title'], 'excerpt': p.get('excerpt', ''),
        'category': p['category'], 'category_label': CATEGORIES.get(p['category'], p['category']),
        'tier': p.get('tier', 'free'), 'cover_image': p.get('cover_image', ''),
        'featured': p.get('featured', False), 'read_time': p.get('read_time', 3),
        'tags': p.get('tags', []),
        'author': p.get('author', AUTHOR), 'published_at': p.get('published_at'),
        'status': p.get('status', 'published'), 'views': p.get('views', 0),
    }


def published_query():
    now = iso(now_utc())
    return {'$or': [
        {'status': 'published'},
        {'status': 'scheduled', 'publish_at': {'$lte': now}},
    ]}


GMAIL_SMTP_USER = os.environ.get('GMAIL_SMTP_USER', '')
GMAIL_SMTP_PASSWORD = os.environ.get('GMAIL_SMTP_PASSWORD', '')
EMAIL_FROM_NAME = os.environ.get('EMAIL_FROM_NAME', 'The Trading Narrative')
EMAIL_REPLY_TO = os.environ.get('EMAIL_REPLY_TO', '')
EMAIL_ENABLED = bool(GMAIL_SMTP_USER and GMAIL_SMTP_PASSWORD)
EMAIL_LAST_ERROR = None  # set when an SMTP send fails, surfaced in admin


def _smtp_send(to: str, subject: str, text: str, html: str = None):
    """Blocking SMTP send — always call via asyncio.to_thread."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f'{EMAIL_FROM_NAME} <{GMAIL_SMTP_USER}>'
    msg['To'] = to
    if EMAIL_REPLY_TO:
        msg['Reply-To'] = EMAIL_REPLY_TO
    msg.attach(MIMEText(text or '', 'plain'))
    if html:
        msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
        server.starttls()
        server.login(GMAIL_SMTP_USER, GMAIL_SMTP_PASSWORD)
        server.sendmail(GMAIL_SMTP_USER, [to], msg.as_string())


async def log_email(to: str, subject: str, body: str, kind: str, html: str = None):
    """Email adapter: real Gmail SMTP when configured; falls back to mocked logging
    on failure so digests/issues never crash the request."""
    global EMAIL_LAST_ERROR
    import asyncio
    status = 'sent (mocked)'
    provider = 'mock'
    if EMAIL_ENABLED:
        provider = 'gmail_smtp'
        try:
            await asyncio.to_thread(_smtp_send, to, subject, body, html)
            status = 'sent (gmail)'
            EMAIL_LAST_ERROR = None
        except Exception as e:
            err = str(e)[:200]
            EMAIL_LAST_ERROR = err
            status = 'failed — logged only'
            logger.warning(f'Gmail SMTP send failed (falling back to log): {err}')
    entry = {
        'id': str(uuid.uuid4()), 'to': to, 'subject': subject, 'body': body,
        'kind': kind, 'provider': provider,
        'sent_at': iso(now_utc()), 'status': status,
    }
    await db.email_logs.insert_one(dict(entry))
    return entry


# ---------------------- schemas ----------------------

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=80)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MagicRequestIn(BaseModel):
    email: EmailStr


class MagicVerifyIn(BaseModel):
    token: str


class CheckoutIn(BaseModel):
    plan: str  # monthly | annual
    origin_url: Optional[str] = None


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    token: str
    password: str = Field(min_length=6)


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[str] = None


class BookmarkToggleIn(BaseModel):
    post_id: str


class NewsletterIn(BaseModel):
    email: EmailStr
    source: str = 'site'


class PostIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    excerpt: str = ''
    category: str
    tier: str = 'free'
    cover_image: str = ''
    content_blocks: List[str] = []
    tags: List[str] = []
    featured: bool = False
    status: str = 'draft'  # draft | published | scheduled
    publish_at: Optional[str] = None


class IssueIn(BaseModel):
    post_id: str
    subject: Optional[str] = None


class TrackIn(BaseModel):
    event: str
    path: str = ''
    meta: dict = {}
    sid: Optional[str] = None  # browser session id for funnel linking


# ---------------------- auth ----------------------

@api_router.post('/auth/register')
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


@api_router.post('/auth/login')
async def login(body: LoginIn):
    user = await db.users.find_one({'email': body.email.lower()})
    if not user or not user.get('password_hash') or not verify_password(body.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    premium = await is_entitled(user)
    return {'token': make_token(user['id']), 'user': public_user(user, premium)}


@api_router.post('/auth/magic-link/request')
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


@api_router.post('/auth/magic-link/verify')
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


@api_router.get('/auth/me')
async def me(user=Depends(get_current_user)):
    premium = await is_entitled(user)
    return {'user': public_user(user, premium)}


@api_router.post('/auth/password-reset/request')
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


@api_router.post('/auth/password-reset/confirm')
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


# ---------------------- posts (public) ----------------------

@api_router.get('/categories')
async def get_categories():
    result = []
    for slug, label in CATEGORIES.items():
        count = await db.posts.count_documents({'category': slug, **published_query()})
        result.append({'slug': slug, 'label': label, 'count': count})
    return result


@api_router.get('/posts')
async def list_posts(category: Optional[str] = None, q: Optional[str] = None,
                     tier: Optional[str] = None, featured: Optional[bool] = None,
                     slugs: Optional[str] = None, tag: Optional[str] = None,
                     limit: int = Query(50, le=100), skip: int = 0):
    query = published_query()
    if tag:
        query['tags'] = tag
    if category:
        query['category'] = category
    if slugs:
        query['slug'] = {'$in': [x for x in slugs.split(',') if x.strip()][:50]}
    if tier in ('free', 'premium'):
        query['tier'] = tier
    if featured is not None:
        query['featured'] = featured
    if q:
        safe = re.escape(q)
        query['$and'] = [{'$or': [
            {'title': {'$regex': safe, '$options': 'i'}},
            {'excerpt': {'$regex': safe, '$options': 'i'}},
        ]}]
    cursor = db.posts.find(query).sort('published_at', -1).skip(skip).limit(limit)
    posts = await cursor.to_list(limit)
    total = await db.posts.count_documents(query)
    return {'posts': [post_summary(clean(p)) for p in posts], 'total': total}


@api_router.get('/posts/{slug}')
async def get_post(slug: str, user=Depends(get_optional_user)):
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    clean(post)
    entitled = await is_entitled(user)
    blocks = post.get('content_blocks', [])
    total_blocks = len(blocks)
    is_locked = post.get('tier') == 'premium' and not entitled
    if is_locked:
        # SERVER-SIDE PAYWALL: only preview paragraphs ever leave the server
        blocks = blocks[:PREVIEW_BLOCKS]
    # related posts: same category, exclude self
    related_cursor = db.posts.find({'category': post['category'], 'slug': {'$ne': slug}, **published_query()}).sort('published_at', -1).limit(3)
    related = [post_summary(clean(r)) for r in await related_cursor.to_list(3)]
    # increment views (fire & forget semantics)
    await db.posts.update_one({'slug': slug}, {'$inc': {'views': 1}})
    result = post_summary(post)
    result.update({
        'content_blocks': blocks,
        'is_locked': is_locked,
        'total_blocks': total_blocks,
        'shown_blocks': len(blocks),
        'related': related,
    })
    return result


# ---------------------- comments (premium members) ----------------------

@api_router.get('/posts/{slug}/comments')
async def list_comments(slug: str):
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    comments = await db.comments.find({'post_id': post['id']}).sort('created_at', -1).to_list(500)
    return {'comments': [clean(c) for c in comments], 'total': len(comments)}


@api_router.post('/posts/{slug}/comments')
async def create_comment(slug: str, body: CommentIn, user=Depends(get_current_user)):
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    entitled = await is_entitled(user)
    if not entitled:
        raise HTTPException(status_code=403, detail='Comments are a Premium member perk. Upgrade to join the discussion.')
    parent_id = None
    replied_to = None
    if body.parent_id:
        parent = await db.comments.find_one({'id': body.parent_id})
        if not parent or parent['post_id'] != post['id']:
            raise HTTPException(status_code=400, detail='Parent comment not found on this post')
        replied_to = parent
        # flatten threads to 2 levels: replying to a reply attaches to its top-level parent
        parent_id = parent.get('parent_id') or parent['id']
    comment = {
        'id': str(uuid.uuid4()), 'post_id': post['id'], 'post_slug': slug,
        'parent_id': parent_id,
        'user_id': user['id'], 'user_name': user.get('name') or user['email'].split('@')[0],
        'is_admin': user.get('role') == 'admin',
        'body': body.body.strip(), 'created_at': iso(now_utc()),
    }
    await db.comments.insert_one(dict(comment))
    # notify the author of the comment being replied to
    if replied_to and replied_to['user_id'] != user['id']:
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()), 'user_id': replied_to['user_id'], 'type': 'reply',
            'actor_name': comment['user_name'], 'post_slug': slug, 'post_title': post['title'],
            'preview': comment['body'][:140], 'comment_id': comment['id'],
            'read': False, 'created_at': iso(now_utc()),
        })
    return clean(comment)


# ---------------------- notifications ----------------------

@api_router.get('/notifications')
async def get_notifications(user=Depends(get_current_user)):
    notifs = await db.notifications.find({'user_id': user['id']}).sort('created_at', -1).limit(50).to_list(50)
    unread = await db.notifications.count_documents({'user_id': user['id'], 'read': False})
    return {'notifications': [clean(n) for n in notifs], 'unread': unread}


@api_router.post('/notifications/mark-read')
async def mark_notifications_read(user=Depends(get_current_user)):
    await db.notifications.update_many({'user_id': user['id'], 'read': False}, {'$set': {'read': True}})
    return {'ok': True}


@api_router.delete('/comments/{comment_id}')
async def delete_comment(comment_id: str, user=Depends(get_current_user)):
    comment = await db.comments.find_one({'id': comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail='Comment not found')
    if comment['user_id'] != user['id'] and user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='You can only delete your own comments')
    await db.comments.delete_one({'id': comment_id})
    # remove orphaned replies of a deleted top-level comment
    await db.comments.delete_many({'parent_id': comment_id})
    return {'ok': True}


# ---------------------- bookmarks (reading list) ----------------------

@api_router.get('/bookmarks')
async def get_bookmarks(user=Depends(get_current_user)):
    marks = await db.bookmarks.find({'user_id': user['id']}).sort('created_at', -1).to_list(500)
    post_ids = [m['post_id'] for m in marks]
    posts_map = {}
    if post_ids:
        posts = await db.posts.find({'id': {'$in': post_ids}, **published_query()}).to_list(500)
        posts_map = {p['id']: post_summary(clean(p)) for p in posts}
    ordered = [posts_map[pid] for pid in post_ids if pid in posts_map]
    return {'posts': ordered, 'post_ids': post_ids}


@api_router.post('/bookmarks/toggle')
async def toggle_bookmark(body: BookmarkToggleIn, user=Depends(get_current_user)):
    post = await db.posts.find_one({'id': body.post_id})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    existing = await db.bookmarks.find_one({'user_id': user['id'], 'post_id': body.post_id})
    if existing:
        await db.bookmarks.delete_one({'id': existing['id']})
        return {'bookmarked': False}
    await db.bookmarks.insert_one({
        'id': str(uuid.uuid4()), 'user_id': user['id'], 'post_id': body.post_id,
        'created_at': iso(now_utc()),
    })
    return {'bookmarked': True}


# ---------------------- recommendations (related by interest) ----------------------

@api_router.get('/recommendations')
async def recommendations(slugs: str = '', limit: int = Query(6, le=12), user=Depends(get_optional_user)):
    read_slugs = [s for s in slugs.split(',') if s.strip()][:50]
    weights = {}
    # weight categories from client-provided reading history
    if read_slugs:
        read_posts = await db.posts.find({'slug': {'$in': read_slugs}}).to_list(100)
        for p in read_posts:
            weights[p['category']] = weights.get(p['category'], 0) + 1
    # plus server-side pageview history for signed-in readers
    if user:
        events = await db.analytics.find(
            {'user_id': user['id'], 'event': 'pageview', 'path': {'$regex': '^/post/'}}
        ).sort('created_at', -1).limit(100).to_list(100)
        seen = set()
        for e in events:
            slug = e['path'].split('/post/')[-1].strip('/')
            if slug and slug not in seen:
                seen.add(slug)
                read_slugs.append(slug)
        if seen:
            hist_posts = await db.posts.find({'slug': {'$in': list(seen)}}).to_list(200)
            for p in hist_posts:
                weights[p['category']] = weights.get(p['category'], 0) + 1
    if not weights:
        return {'posts': [], 'based_on': []}
    candidates = await db.posts.find({**published_query(), 'slug': {'$nin': read_slugs}}).to_list(500)
    scored = sorted(
        candidates,
        key=lambda p: (-(weights.get(p['category'], 0)), p.get('published_at') or ''),
    )
    scored = [p for p in scored if weights.get(p['category'], 0) > 0]
    top_categories = sorted(weights, key=weights.get, reverse=True)[:2]
    return {
        'posts': [post_summary(clean(p)) for p in scored[:limit]],
        'based_on': [CATEGORIES.get(c, c) for c in top_categories],
    }


# ---------------------- billing (Stripe via emergentintegrations) ----------------------

def stripe_client(webhook_url: Optional[str] = None) -> StripeCheckout:
    return StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url or f'{FRONTEND_URL}/api/webhook/stripe')


async def activate_premium_from_transaction(txn):
    """Idempotently activate premium for the user who paid for this transaction."""
    if txn.get('activated'):
        return
    res = await db.payment_transactions.update_one(
        {'session_id': txn['session_id'], 'activated': {'$ne': True}},
        {'$set': {'activated': True, 'updated_at': iso(now_utc())}},
    )
    if res.modified_count == 0:
        return  # another path won the race
    plan_id = txn['plan']
    plan = PLANS[plan_id]
    user = await db.users.find_one({'id': txn['user_id']})
    if not user:
        return
    existing = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if not existing:
        auto_renew = bool(txn.get('auto_renew'))
        period_end = now_utc() + timedelta(days=plan['period_days'])
        stripe_sub_id = txn.get('stripe_subscription_id')
        rzp_sub_id = txn['session_id'] if txn.get('kind') == 'subscription' else None
        if auto_renew and stripe_sub_id:
            try:
                sdk = configure_stripe_sdk()
                s = sdk.Subscription.retrieve(stripe_sub_id)
                if s.get('current_period_end'):
                    period_end = datetime.fromtimestamp(s['current_period_end'], tz=timezone.utc)
            except Exception as e:
                logger.warning(f'Could not fetch Stripe subscription period end: {e}')
        sub = {
            'id': str(uuid.uuid4()), 'user_id': user['id'], 'plan': plan_id,
            'status': 'active', 'provider': 'stripe',
            'auto_renew': auto_renew,
            'stripe_session_id': txn['session_id'],
            'stripe_subscription_id': stripe_sub_id,
            'razorpay_subscription_id': rzp_sub_id,
            'gateway': txn.get('provider', 'stripe'),
            'current_period_start': iso(now_utc()),
            'current_period_end': iso(period_end),
            'created_at': iso(now_utc()), 'canceled_at': None,
        }
        await db.subscriptions.insert_one(dict(sub))
    invoice = {
        'id': str(uuid.uuid4()), 'user_id': user['id'],
        'subscription_id': txn['session_id'],
        'number': f"TTN-{now_utc().strftime('%Y%m')}-{random.randint(1000, 9999)}",
        'amount': txn.get('amount', plan['amount']),
        'currency': txn.get('currency', plan['currency']), 'plan': plan_id,
        'status': 'paid', 'created_at': iso(now_utc()),
    }
    await db.invoices.insert_one(dict(invoice))
    await db.analytics.insert_one({'id': str(uuid.uuid4()), 'event': 'checkout_complete',
                                   'path': '/pricing', 'meta': {'plan': plan_id},
                                   'user_id': user['id'], 'created_at': iso(now_utc())})
    await log_email(user['email'], 'Welcome to Premium — The Trading Narrative',
                    f"Your {plan['label']} pass is active. Enjoy full access.", 'premium_welcome')


@api_router.get('/billing/config')
async def billing_config():
    await maybe_reprobe_razorpay()
    return {'mock_mode': MOCK_BILLING, 'auto_renew': AUTO_RENEW,
            'razorpay_enabled': RAZORPAY_ENABLED, 'razorpay_key_id': RAZORPAY_KEY_ID or None,
            'razorpay_autopay': RAZORPAY_SUBS_ENABLED,
            'plans': list(PLANS.values())}


@api_router.post('/billing/checkout')
async def checkout(body: CheckoutIn, user=Depends(get_current_user)):
    if body.plan not in PLANS:
        raise HTTPException(status_code=400, detail='Invalid plan')
    existing = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail='You already have an active subscription')
    plan = PLANS[body.plan]

    if MOCK_BILLING:
        # MOCKED fallback path (MOCK_BILLING=true)
        period_days = plan['period_days']
        sub = {
            'id': str(uuid.uuid4()), 'user_id': user['id'], 'plan': body.plan,
            'status': 'active', 'provider': 'mock',
            'current_period_start': iso(now_utc()),
            'current_period_end': iso(now_utc() + timedelta(days=period_days)),
            'created_at': iso(now_utc()), 'canceled_at': None,
        }
        await db.subscriptions.insert_one(dict(sub))
        invoice = {
            'id': str(uuid.uuid4()), 'user_id': user['id'], 'subscription_id': sub['id'],
            'number': f"TTN-{now_utc().strftime('%Y%m')}-{random.randint(1000, 9999)}",
            'amount': plan['amount'], 'currency': plan['currency'], 'plan': body.plan,
            'status': 'paid', 'created_at': iso(now_utc()),
        }
        await db.invoices.insert_one(dict(invoice))
        await log_email(user['email'], 'Welcome to Premium — The Trading Narrative',
                        f"Your {plan['label']} subscription is active.", 'premium_welcome')
        return {'ok': True, 'mock': True, 'subscription': clean(sub), 'invoice': clean(invoice)}

    # REAL STRIPE CHECKOUT (test mode)
    origin = (body.origin_url or FRONTEND_URL).rstrip('/')
    success_url = f'{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = f'{origin}/payment/cancel'
    metadata = {'user_id': user['id'], 'plan': body.plan, 'app': 'trading-narrative'}
    try:
        if AUTO_RENEW:
            # TRUE AUTO-RENEWING SUBSCRIPTION (user's own Stripe key)
            sdk = configure_stripe_sdk()
            session_obj = sdk.checkout.Session.create(
                mode='subscription',
                line_items=[{
                    'price_data': {
                        'currency': plan['currency'],
                        'unit_amount': int(round(plan['amount'] * 100)),
                        'recurring': {'interval': plan['interval']},
                        'product_data': {'name': f"The Trading Narrative Premium — {plan['label']}"},
                    },
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
            session_url, session_id = session_obj.url, session_obj.id
        else:
            # One-time timed pass (shared Emergent test key — Stripe-side cancel API unavailable)
            checkout_req = CheckoutSessionRequest(
                amount=float(plan['amount']),
                currency=plan['currency'],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
            session = await stripe_client().create_checkout_session(checkout_req)
            session_url, session_id = session.url, session.session_id
    except Exception as e:
        logger.error(f'Stripe checkout creation failed: {e}')
        raise HTTPException(status_code=502, detail='Could not start Stripe checkout. Please try again.')
    await db.payment_transactions.insert_one({
        'session_id': session_id, 'user_id': user['id'], 'plan': body.plan,
        'amount': plan['amount'], 'currency': plan['currency'],
        'auto_renew': AUTO_RENEW,
        'status': 'initiated', 'payment_status': 'pending', 'activated': False,
        'created_at': iso(now_utc()), 'updated_at': iso(now_utc()),
    })
    return {'ok': True, 'mock': False, 'checkout_url': session_url, 'session_id': session_id}


@api_router.get('/payments/status/{session_id}')
async def payment_status(session_id: str):
    record = await db.payment_transactions.find_one({'session_id': session_id})
    if not record:
        raise HTTPException(status_code=404, detail='Transaction not found')
    if record.get('payment_status') != 'paid':
        try:
            sdk = configure_stripe_sdk()
            s = sdk.checkout.Session.retrieve(session_id)
            if s.payment_status == 'paid' or s.status == 'complete':
                await db.payment_transactions.update_one(
                    {'session_id': session_id, 'payment_status': {'$ne': 'paid'}},
                    {'$set': {'status': 'completed', 'payment_status': 'paid',
                              'stripe_subscription_id': s.get('subscription'),
                              'updated_at': iso(now_utc())}},
                )
                record = await db.payment_transactions.find_one({'session_id': session_id})
            elif s.status == 'expired':
                await db.payment_transactions.update_one(
                    {'session_id': session_id},
                    {'$set': {'status': 'expired', 'payment_status': 'expired',
                              'updated_at': iso(now_utc())}},
                )
                record = await db.payment_transactions.find_one({'session_id': session_id})
        except Exception as e:
            logger.warning(f'Stripe status check failed for {session_id}: {e}')
    if record.get('payment_status') == 'paid':
        await activate_premium_from_transaction(record)
    return {'session_id': record['session_id'], 'status': record['status'],
            'payment_status': record['payment_status']}


@api_router.post('/webhook/stripe')
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get('Stripe-Signature')
    try:
        event = await stripe_client(str(request.base_url).rstrip('/') + '/api/webhook/stripe').handle_webhook(body, signature)
    except Exception as e:
        logger.warning(f'Stripe webhook rejected: {e}')
        raise HTTPException(status_code=400, detail='Invalid webhook')
    if event.session_id and event.payment_status == 'paid':
        await db.payment_transactions.update_one(
            {'session_id': event.session_id, 'payment_status': {'$ne': 'paid'}},
            {'$set': {'status': 'completed', 'payment_status': 'paid', 'updated_at': iso(now_utc())}},
        )
        record = await db.payment_transactions.find_one({'session_id': event.session_id})
        if record:
            await activate_premium_from_transaction(record)
    return {'status': 'ok'}


@api_router.post('/billing/cancel')
async def cancel_subscription(user=Depends(get_current_user)):
    sub = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if not sub:
        raise HTTPException(status_code=400, detail='No active subscription')
    # Cancel the recurring Razorpay Autopay mandate too
    if sub.get('auto_renew') and sub.get('razorpay_subscription_id') and RAZORPAY_ENABLED:
        try:
            import asyncio
            await asyncio.to_thread(lambda: razorpay_client().subscription.cancel(sub['razorpay_subscription_id']))
        except Exception as e:
            logger.warning(f'Razorpay subscription cancel failed (continuing with local cancel): {e}')
    # Cancel the recurring subscription at Stripe too (own-key auto-renew mode)
    if sub.get('auto_renew') and sub.get('stripe_subscription_id') and not IS_SHARED_STRIPE_KEY:
        try:
            sdk = configure_stripe_sdk()
            sdk.Subscription.delete(sub['stripe_subscription_id'])
        except Exception as e:
            logger.warning(f'Stripe subscription cancel failed (continuing with local cancel): {e}')
    await db.subscriptions.update_one({'id': sub['id']}, {'$set': {'status': 'canceled', 'canceled_at': iso(now_utc())}})
    return {'ok': True, 'message': 'Subscription canceled. Premium access removed.'}


@api_router.get('/billing/subscription')
async def get_subscription(user=Depends(get_current_user)):
    sub = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    return {'subscription': clean(sub), 'is_premium': await is_entitled(user)}


@api_router.get('/billing/invoices')
async def get_invoices(user=Depends(get_current_user)):
    invoices = await db.invoices.find({'user_id': user['id']}).sort('created_at', -1).to_list(100)
    return {'invoices': [clean(i) for i in invoices]}


# ---------------------- newsletter (MOCKED provider) ----------------------

@api_router.post('/newsletter/subscribe')
async def newsletter_subscribe(body: NewsletterIn):
    email = body.email.lower()
    existing = await db.newsletter_subscribers.find_one({'email': email})
    if existing:
        return {'ok': True, 'message': "You're already subscribed!", 'already': True}
    await db.newsletter_subscribers.insert_one({
        'id': str(uuid.uuid4()), 'email': email, 'source': body.source,
        'status': 'subscribed', 'created_at': iso(now_utc()),
    })
    await log_email(email, 'Welcome to The Trading Narrative',
                    'Thanks for subscribing! Expect sharp insights on tech, markets, and living well.', 'welcome')
    await db.analytics.insert_one({'id': str(uuid.uuid4()), 'event': 'newsletter_subscribe',
                                   'path': body.source, 'meta': {}, 'user_id': None,
                                   'created_at': iso(now_utc())})
    return {'ok': True, 'message': "You're in! Check your inbox for a welcome note.", 'already': False}


class NewsletterPrefsIn(BaseModel):
    subscribed: bool = True
    categories: List[str] = []


@api_router.get('/newsletter/my-preferences')
async def my_newsletter_prefs(user=Depends(get_current_user)):
    sub = await db.newsletter_subscribers.find_one({'email': user['email']})
    if not sub:
        return {'subscribed': False, 'categories': list(CATEGORIES.keys())}
    return {'subscribed': sub.get('status') == 'subscribed',
            'categories': sub.get('categories', list(CATEGORIES.keys()))}


@api_router.post('/newsletter/my-preferences')
async def set_newsletter_prefs(body: NewsletterPrefsIn, user=Depends(get_current_user)):
    cats = [c for c in body.categories if c in CATEGORIES] or list(CATEGORIES.keys())
    sub = await db.newsletter_subscribers.find_one({'email': user['email']})
    if not sub:
        await db.newsletter_subscribers.insert_one({
            'id': str(uuid.uuid4()), 'email': user['email'], 'source': 'account',
            'status': 'subscribed' if body.subscribed else 'unsubscribed',
            'categories': cats, 'created_at': iso(now_utc()),
        })
    else:
        await db.newsletter_subscribers.update_one({'email': user['email']}, {'$set': {
            'status': 'subscribed' if body.subscribed else 'unsubscribed',
            'categories': cats,
        }})
    return {'ok': True, 'subscribed': body.subscribed, 'categories': cats}


# ---------------------- analytics ----------------------

@api_router.post('/analytics/track')
async def track(body: TrackIn, request: Request, user=Depends(get_optional_user)):
    doc = {
        'id': str(uuid.uuid4()), 'event': body.event, 'path': body.path,
        'meta': body.meta, 'user_id': user['id'] if user else None,
        'sid': body.sid, 'created_at': iso(now_utc()),
    }
    # Traffic source attribution — only on the first pageview of a browser session
    meta = body.meta or {}
    if body.event == 'pageview' and meta.get('first_visit'):
        referrer = (meta.get('referrer') or request.headers.get('referer', '') or '').strip()
        utm_source = (meta.get('utm_source') or '').strip()
        source, ref_host = classify_traffic_source(referrer, utm_source)
        if source:
            doc['source'] = source
            doc['referrer_host'] = ref_host
            if utm_source:
                doc['utm_source'] = utm_source
            if meta.get('utm_medium'):
                doc['utm_medium'] = meta['utm_medium']
            if meta.get('utm_campaign'):
                doc['utm_campaign'] = meta['utm_campaign']
    await db.analytics.insert_one(doc)
    return {'ok': True}


@api_router.get('/admin/traffic')
async def admin_traffic(admin=Depends(get_admin_user), days: int = Query(30, le=365)):
    since = iso(now_utc() - timedelta(days=days))
    match = {'source': {'$exists': True, '$ne': None}, 'created_at': {'$gte': since}}
    rows = await db.analytics.aggregate([
        {'$match': match},
        {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
    ]).to_list(50)
    total = sum(r['count'] for r in rows) or 0
    sources = [{'source': r['_id'], 'count': r['count'],
                'pct': round(r['count'] * 100 / total, 1) if total else 0} for r in rows]
    referrers = await db.analytics.aggregate([
        {'$match': {**match, 'referrer_host': {'$nin': ['', None]}}},
        {'$group': {'_id': '$referrer_host', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}, {'$limit': 10},
    ]).to_list(10)
    campaigns = await db.analytics.aggregate([
        {'$match': {**match, 'utm_campaign': {'$exists': True, '$nin': ['', None]}}},
        {'$group': {'_id': {'campaign': '$utm_campaign', 'source': '$source'}, 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}, {'$limit': 10},
    ]).to_list(10)
    # weekly trend for the top 5 sources (everything else grouped as 'Other')
    top_sources = [s['source'] for s in sources[:5]]
    docs = await db.analytics.find(match, {'source': 1, 'created_at': 1}).to_list(20000)
    weeks = {}
    for d in docs:
        try:
            dt = datetime.fromisoformat(d['created_at'])
        except Exception:
            continue
        week_start = (dt - timedelta(days=dt.weekday())).date()
        label = week_start.strftime('%b %d')
        key = (week_start, label)
        src = d['source'] if d['source'] in top_sources else 'Other'
        weeks.setdefault(key, {})
        weeks[key][src] = weeks[key].get(src, 0) + 1
    trend_series = list(top_sources)
    if any('Other' in v for v in weeks.values()) and 'Other' not in trend_series:
        trend_series.append('Other')
    trend = []
    for (ws, label) in sorted(weeks.keys()):
        row = {'week': label}
        for s in trend_series:
            row[s] = weeks[(ws, label)].get(s, 0)
        trend.append(row)
    # post attribution: which pages visitors landed on, per source
    pages = await db.analytics.aggregate([
        {'$match': match},
        {'$group': {'_id': {'path': '$path', 'source': '$source'}, 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}, {'$limit': 15},
    ]).to_list(15)
    landing_pages = [{'path': p['_id']['path'] or '/', 'source': p['_id']['source'],
                      'count': p['count']} for p in pages]
    return {
        'days': days, 'total_visits': total, 'sources': sources,
        'top_referrers': [{'host': r['_id'], 'count': r['count']} for r in referrers],
        'campaigns': [{'campaign': c['_id']['campaign'], 'source': c['_id']['source'],
                       'count': c['count']} for c in campaigns],
        'trend': trend, 'trend_series': trend_series,
        'landing_pages': landing_pages,
    }


@api_router.get('/admin/traffic/export')
async def admin_traffic_export(admin=Depends(get_admin_user), days: int = Query(30, le=365)):
    data = await admin_traffic(admin=admin, days=days)
    import csv as _csv
    import io as _io
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow(['section', 'name', 'source', 'visits', 'share_pct'])
    for s in data['sources']:
        w.writerow(['source', s['source'], '', s['count'], s['pct']])
    for r in data['top_referrers']:
        w.writerow(['referrer', r['host'], '', r['count'], ''])
    for c in data['campaigns']:
        w.writerow(['campaign', c['campaign'], c['source'], c['count'], ''])
    for p in data['landing_pages']:
        w.writerow(['landing_page', p['path'], p['source'], p['count'], ''])
    filename = f'traffic-sources-{days}d-{now_utc().strftime("%Y%m%d")}.csv'
    return Response(content=buf.getvalue(), media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@api_router.get('/admin/funnel')
async def admin_funnel(admin=Depends(get_admin_user), days: int = Query(30, le=365)):
    """Conversion funnel per traffic source: arrived → viewed pricing → started checkout → went premium.
    Linked via browser session ids; premium matched through the session's user_id."""
    since = iso(now_utc() - timedelta(days=days))
    # 1) attributed sessions: sid -> source
    entries = await db.analytics.find(
        {'source': {'$exists': True, '$ne': None}, 'sid': {'$nin': [None, '']},
         'created_at': {'$gte': since}},
        {'sid': 1, 'source': 1}).to_list(20000)
    sid_source = {}
    for e in entries:
        sid_source.setdefault(e['sid'], e['source'])
    sids = list(sid_source.keys())
    if not sids:
        return {'days': days, 'total_sessions': 0, 'funnel': [], 'overall': None}
    # 2) all events for those sessions
    events = await db.analytics.find(
        {'sid': {'$in': sids}, 'created_at': {'$gte': since}},
        {'sid': 1, 'event': 1, 'path': 1, 'user_id': 1}).to_list(100000)
    sessions = {}
    for ev in events:
        s = sessions.setdefault(ev['sid'], {'pricing': False, 'cta': False, 'user_ids': set()})
        if ev['event'] == 'pageview' and (ev.get('path') or '').startswith('/pricing'):
            s['pricing'] = True
        if ev['event'] == 'subscribe_cta_click':
            s['cta'] = True
        if ev.get('user_id'):
            s['user_ids'].add(ev['user_id'])
    # 3) which users converted (checkout completed) in the window
    conv_events = await db.analytics.find(
        {'event': 'checkout_complete', 'created_at': {'$gte': since}},
        {'user_id': 1}).to_list(10000)
    converted_users = {c['user_id'] for c in conv_events if c.get('user_id')}
    # 4) aggregate per source
    per_source = {}
    for sid, src in sid_source.items():
        s = sessions.get(sid, {'pricing': False, 'cta': False, 'user_ids': set()})
        row = per_source.setdefault(src, {'source': src, 'visits': 0, 'pricing_views': 0,
                                          'checkouts_started': 0, 'conversions': 0})
        row['visits'] += 1
        if s['pricing']:
            row['pricing_views'] += 1
        if s['cta']:
            row['checkouts_started'] += 1
        if s['user_ids'] & converted_users:
            row['conversions'] += 1
    funnel = sorted(per_source.values(), key=lambda r: -r['visits'])
    for r in funnel:
        r['conversion_rate'] = round(r['conversions'] * 100 / r['visits'], 1) if r['visits'] else 0
    overall = {
        'visits': sum(r['visits'] for r in funnel),
        'pricing_views': sum(r['pricing_views'] for r in funnel),
        'checkouts_started': sum(r['checkouts_started'] for r in funnel),
        'conversions': sum(r['conversions'] for r in funnel),
    }
    return {'days': days, 'total_sessions': len(sids), 'funnel': funnel, 'overall': overall}


# ---------------------- community lounge (premium members only) ----------------------

async def get_premium_user(user=Depends(get_current_user)):
    if not await is_entitled(user):
        raise HTTPException(status_code=403, detail='The Lounge is for Premium members. Upgrade to join the conversation.')
    return user


class AnnouncementIn(BaseModel):
    title: str
    body: str
    publish_at: Optional[str] = None  # ISO datetime — schedule for later


class CommunityThreadIn(BaseModel):
    title: str
    body: str


class CommunityReplyIn(BaseModel):
    body: str


def community_author(user):
    return {'id': user['id'], 'name': user.get('name') or user['email'].split('@')[0],
            'role': user.get('role', 'user')}


@api_router.get('/community/announcements')
async def community_announcements(user=Depends(get_premium_user)):
    items = await db.community_announcements.find({}).sort('created_at', -1).to_list(50)
    now = iso(now_utc())
    out = []
    for a in items:
        clean(a)
        scheduled = bool(a.get('publish_at') and a['publish_at'] > now)
        if scheduled and user.get('role') != 'admin':
            continue  # members only see published announcements
        a['scheduled'] = scheduled
        out.append(a)
    return {'announcements': out}


@api_router.post('/community/announcements')
async def community_create_announcement(body: AnnouncementIn, admin=Depends(get_admin_user)):
    title, text = body.title.strip(), body.body.strip()
    if not (3 <= len(title) <= 200):
        raise HTTPException(status_code=400, detail='Title must be 3-200 characters')
    if not (1 <= len(text) <= 5000):
        raise HTTPException(status_code=400, detail='Body must be 1-5000 characters')
    publish_at = None
    if body.publish_at:
        try:
            dt = datetime.fromisoformat(body.publish_at.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            publish_at = iso(dt)
        except Exception:
            raise HTTPException(status_code=400, detail='Invalid publish_at datetime')
    item = {'id': str(uuid.uuid4()), 'title': title, 'body': text,
            'author': community_author(admin), 'publish_at': publish_at,
            'created_at': iso(now_utc())}
    await db.community_announcements.insert_one(dict(item))
    item = clean(item)
    item['scheduled'] = bool(publish_at and publish_at > iso(now_utc()))
    return item


@api_router.delete('/community/announcements/{aid}')
async def community_delete_announcement(aid: str, admin=Depends(get_admin_user)):
    result = await db.community_announcements.delete_one({'id': aid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Announcement not found')
    return {'ok': True}


@api_router.get('/community/members/{uid}')
async def community_member_profile(uid: str, user=Depends(get_premium_user)):
    member = await db.users.find_one({'id': uid})
    if not member:
        raise HTTPException(status_code=404, detail='Member not found')
    premium = await is_entitled(member)
    thread_count = await db.community_threads.count_documents({'author.id': uid})
    reply_count = await db.community_replies.count_documents({'author.id': uid})
    recent = await db.community_threads.find({'author.id': uid}).sort('created_at', -1).limit(5).to_list(5)
    return {
        'id': member['id'],
        'name': member.get('name') or member['email'].split('@')[0],
        'role': member.get('role', 'user'),
        'is_premium': premium,
        'joined': member.get('created_at'),
        'thread_count': thread_count,
        'reply_count': reply_count,
        'recent_threads': [{'id': t['id'], 'title': t['title'], 'created_at': t['created_at'],
                            'reply_count': t.get('reply_count', 0)} for t in recent],
    }


@api_router.get('/community/threads')
async def community_threads(user=Depends(get_premium_user)):
    threads = await db.community_threads.find({}).sort(
        [('pinned', -1), ('last_activity_at', -1)]).to_list(100)
    return {'threads': [clean(t) for t in threads]}


@api_router.post('/community/threads')
async def community_create_thread(body: CommunityThreadIn, user=Depends(get_premium_user)):
    title, text = body.title.strip(), body.body.strip()
    if not (3 <= len(title) <= 200):
        raise HTTPException(status_code=400, detail='Title must be 3-200 characters')
    if not (1 <= len(text) <= 5000):
        raise HTTPException(status_code=400, detail='Body must be 1-5000 characters')
    # basic rate limit: max 5 threads per hour per member
    hour_ago = iso(now_utc() - timedelta(hours=1))
    recent = await db.community_threads.count_documents({'author.id': user['id'], 'created_at': {'$gte': hour_ago}})
    if recent >= 5:
        raise HTTPException(status_code=429, detail='Slow down — you can start up to 5 discussions per hour.')
    thread = {'id': str(uuid.uuid4()), 'title': title, 'body': text,
              'author': community_author(user), 'reply_count': 0, 'pinned': False, 'locked': False,
              'created_at': iso(now_utc()), 'last_activity_at': iso(now_utc())}
    await db.community_threads.insert_one(dict(thread))
    return clean(thread)


@api_router.get('/community/threads/{tid}')
async def community_thread_detail(tid: str, user=Depends(get_premium_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    replies = await db.community_replies.find({'thread_id': tid}).sort('created_at', 1).to_list(500)
    return {'thread': clean(thread), 'replies': [clean(r) for r in replies]}


@api_router.post('/community/threads/{tid}/replies')
async def community_reply(tid: str, body: CommunityReplyIn, user=Depends(get_premium_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    if thread.get('locked'):
        raise HTTPException(status_code=403, detail='This discussion is locked — it stays readable but no new replies.')
    text = body.body.strip()
    if not (1 <= len(text) <= 5000):
        raise HTTPException(status_code=400, detail='Reply must be 1-5000 characters')
    hour_ago = iso(now_utc() - timedelta(hours=1))
    recent = await db.community_replies.count_documents({'author.id': user['id'], 'created_at': {'$gte': hour_ago}})
    if recent >= 30:
        raise HTTPException(status_code=429, detail='Slow down — up to 30 replies per hour.')
    reply = {'id': str(uuid.uuid4()), 'thread_id': tid, 'body': text,
             'author': community_author(user), 'created_at': iso(now_utc())}
    await db.community_replies.insert_one(dict(reply))
    await db.community_threads.update_one({'id': tid}, {
        '$inc': {'reply_count': 1}, '$set': {'last_activity_at': iso(now_utc())}})
    # bell notification for the discussion author
    if thread['author']['id'] != user['id']:
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()), 'user_id': thread['author']['id'], 'type': 'lounge_reply',
            'actor_name': reply['author']['name'], 'thread_id': tid, 'thread_title': thread['title'],
            'preview': text[:140], 'read': False, 'created_at': iso(now_utc()),
        })
    return clean(reply)


@api_router.post('/community/threads/{tid}/pin')
async def community_pin_thread(tid: str, admin=Depends(get_admin_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    new_state = not thread.get('pinned', False)
    await db.community_threads.update_one({'id': tid}, {'$set': {'pinned': new_state}})
    return {'ok': True, 'pinned': new_state}


@api_router.post('/community/threads/{tid}/lock')
async def community_lock_thread(tid: str, admin=Depends(get_admin_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    new_state = not thread.get('locked', False)
    await db.community_threads.update_one({'id': tid}, {'$set': {'locked': new_state}})
    return {'ok': True, 'locked': new_state}


@api_router.delete('/community/threads/{tid}')
async def community_delete_thread(tid: str, user=Depends(get_premium_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    if user.get('role') != 'admin' and thread['author']['id'] != user['id']:
        raise HTTPException(status_code=403, detail='You can only delete your own threads')
    await db.community_threads.delete_one({'id': tid})
    await db.community_replies.delete_many({'thread_id': tid})
    return {'ok': True}


@api_router.delete('/community/replies/{rid}')
async def community_delete_reply(rid: str, user=Depends(get_premium_user)):
    reply = await db.community_replies.find_one({'id': rid})
    if not reply:
        raise HTTPException(status_code=404, detail='Reply not found')
    if user.get('role') != 'admin' and reply['author']['id'] != user['id']:
        raise HTTPException(status_code=403, detail='You can only delete your own replies')
    await db.community_replies.delete_one({'id': rid})
    await db.community_threads.update_one({'id': reply['thread_id']}, {'$inc': {'reply_count': -1}})
    return {'ok': True}


# ---------------------- admin ----------------------

@api_router.get('/admin/posts')
async def admin_list_posts(admin=Depends(get_admin_user)):
    posts = await db.posts.find({}).sort('created_at', -1).to_list(500)
    out = []
    for p in posts:
        clean(p)
        s = post_summary(p)
        s['publish_at'] = p.get('publish_at')
        s['created_at'] = p.get('created_at')
        out.append(s)
    return {'posts': out}


@api_router.get('/admin/posts/{post_id}')
async def admin_get_post(post_id: str, admin=Depends(get_admin_user)):
    post = await db.posts.find_one({'id': post_id})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    return clean(post)


@api_router.post('/admin/posts')
async def admin_create_post(body: PostIn, admin=Depends(get_admin_user)):
    if body.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail='Invalid category')
    if body.tier not in ('free', 'premium'):
        raise HTTPException(status_code=400, detail='Invalid tier')
    if body.status not in ('draft', 'published', 'scheduled'):
        raise HTTPException(status_code=400, detail='Invalid status')
    if body.status == 'scheduled' and not body.publish_at:
        raise HTTPException(status_code=400, detail='Scheduled posts need a publish_at datetime')
    slug = slugify(body.title)
    if await db.posts.find_one({'slug': slug}):
        slug = f'{slug}-{str(uuid.uuid4())[:6]}'
    post = {
        'id': str(uuid.uuid4()), 'slug': slug, 'title': body.title, 'excerpt': body.excerpt,
        'category': body.category, 'tier': body.tier, 'cover_image': body.cover_image,
        'content_blocks': body.content_blocks, 'tags': [t.strip() for t in body.tags if t.strip()][:10],
        'featured': body.featured,
        'status': body.status, 'publish_at': body.publish_at,
        'published_at': iso(now_utc()) if body.status == 'published' else (body.publish_at or iso(now_utc())),
        'author': AUTHOR, 'read_time': read_time(body.content_blocks), 'views': 0,
        'created_at': iso(now_utc()), 'updated_at': iso(now_utc()),
    }
    await db.posts.insert_one(dict(post))
    return clean(post)


@api_router.put('/admin/posts/{post_id}')
async def admin_update_post(post_id: str, body: PostIn, admin=Depends(get_admin_user)):
    post = await db.posts.find_one({'id': post_id})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    if body.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail='Invalid category')
    updates = {
        'title': body.title, 'excerpt': body.excerpt, 'category': body.category,
        'tier': body.tier, 'cover_image': body.cover_image, 'content_blocks': body.content_blocks,
        'tags': [t.strip() for t in body.tags if t.strip()][:10],
        'featured': body.featured, 'status': body.status, 'publish_at': body.publish_at,
        'read_time': read_time(body.content_blocks), 'updated_at': iso(now_utc()),
    }
    if body.status == 'published' and post.get('status') != 'published':
        updates['published_at'] = iso(now_utc())
    await db.posts.update_one({'id': post_id}, {'$set': updates})
    updated = await db.posts.find_one({'id': post_id})
    return clean(updated)


@api_router.delete('/admin/posts/{post_id}')
async def admin_delete_post(post_id: str, admin=Depends(get_admin_user)):
    result = await db.posts.delete_one({'id': post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Post not found')
    return {'ok': True}


@api_router.get('/admin/newsletter/subscribers')
async def admin_subscribers(admin=Depends(get_admin_user)):
    subs = await db.newsletter_subscribers.find({}).sort('created_at', -1).to_list(1000)
    return {'subscribers': [clean(s) for s in subs], 'total': len(subs)}


@api_router.post('/admin/newsletter/issues')
async def admin_send_issue(body: IssueIn, admin=Depends(get_admin_user)):
    post = await db.posts.find_one({'id': body.post_id})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    subs = await db.newsletter_subscribers.find({'status': 'subscribed'}).to_list(10000)
    # respect per-category email preferences (missing prefs = all categories)
    subs = [x for x in subs if post['category'] in x.get('categories', list(CATEGORIES.keys()))]
    subject = body.subject or f"New on The Trading Narrative: {post['title']}"
    post_url = f"{FRONTEND_URL}/post/{post['slug']}"
    # MOCKED SEND: log one email per subscriber
    for s in subs:
        await log_email(s['email'], subject, f"{post.get('excerpt', '')}\n\nRead: {post_url}", 'issue')
    issue = {
        'id': str(uuid.uuid4()), 'post_id': post['id'], 'post_title': post['title'],
        'subject': subject, 'recipients': len(subs), 'status': 'sent (mocked)',
        'sent_at': iso(now_utc()),
    }
    await db.newsletter_issues.insert_one(dict(issue))
    return clean(issue)


@api_router.get('/admin/newsletter/issues')
async def admin_issues(admin=Depends(get_admin_user)):
    issues = await db.newsletter_issues.find({}).sort('sent_at', -1).to_list(200)
    return {'issues': [clean(i) for i in issues]}


@api_router.get('/admin/analytics/stats')
async def admin_stats(admin=Depends(get_admin_user)):
    pageviews = await db.analytics.count_documents({'event': 'pageview'})
    nl_subs = await db.newsletter_subscribers.count_documents({})
    users = await db.users.count_documents({})
    premium = await db.subscriptions.count_documents({'status': 'active'})
    checkouts = await db.analytics.count_documents({'event': 'checkout_complete'})
    cta_clicks = await db.analytics.count_documents({'event': 'subscribe_cta_click'})
    top_posts = await db.posts.find(published_query()).sort('views', -1).limit(5).to_list(5)
    week_ago = iso(now_utc() - timedelta(days=7))
    pageviews_7d = await db.analytics.count_documents({'event': 'pageview', 'created_at': {'$gte': week_ago}})
    return {
        'pageviews': pageviews, 'pageviews_7d': pageviews_7d,
        'newsletter_subscribers': nl_subs, 'users': users,
        'premium_subscribers': premium, 'checkouts': checkouts,
        'subscribe_cta_clicks': cta_clicks,
        'top_posts': [{'title': p['title'], 'slug': p['slug'], 'views': p.get('views', 0)} for p in top_posts],
    }


@api_router.get('/admin/email/status')
async def email_status(admin=Depends(get_admin_user)):
    last_error = EMAIL_LAST_ERROR
    verified = False
    if EMAIL_ENABLED:
        # reflect the most recent real send attempt (survives restarts)
        last_real = await db.email_logs.find_one({'provider': 'gmail_smtp'}, sort=[('sent_at', -1)])
        if last_real:
            if last_real['status'].startswith('failed') and not last_error:
                last_error = 'Last send attempt failed — Gmail requires an App Password.'
            verified = last_real['status'] == 'sent (gmail)'
    return {'enabled': EMAIL_ENABLED, 'provider': 'gmail_smtp' if EMAIL_ENABLED else 'mock',
            'from': f'{EMAIL_FROM_NAME} <{GMAIL_SMTP_USER}>' if EMAIL_ENABLED else None,
            'reply_to': EMAIL_REPLY_TO or None, 'last_error': last_error, 'verified': verified}


@api_router.post('/admin/email/test')
async def email_test(admin=Depends(get_admin_user)):
    entry = await log_email(GMAIL_SMTP_USER or admin['email'],
                            'Test email — The Trading Narrative',
                            'If you are reading this, real email sending works.',
                            'test',
                            html='<p>If you are reading this, <strong>real email sending works</strong>. — The Trading Narrative</p>')
    return {'status': entry['status'], 'to': entry['to'], 'last_error': EMAIL_LAST_ERROR}


@api_router.get('/admin/email-logs')
async def admin_email_logs(admin=Depends(get_admin_user), limit: int = Query(50, le=200)):
    logs = await db.email_logs.find({}).sort('sent_at', -1).limit(limit).to_list(limit)
    return {'logs': [clean(l) for l in logs]}






# ---------------------- Razorpay (INR / UPI) — MOCKED until keys provided ----------------------

class RazorpayCheckoutIn(BaseModel):
    plan: str


class RazorpayVerifyIn(BaseModel):
    order_id: str
    payment_id: Optional[str] = None
    signature: Optional[str] = None


@api_router.post('/billing/razorpay/checkout')
async def razorpay_checkout(body: RazorpayCheckoutIn, user=Depends(get_current_user)):
    if body.plan not in PLANS:
        raise HTTPException(status_code=400, detail='Invalid plan')
    existing = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail='You already have an active subscription')
    plan = PLANS[body.plan]
    amount_paise = int(round(plan['amount_inr'] * 100))
    import asyncio
    await maybe_reprobe_razorpay()  # switch to Autopay live once enabled on the dashboard
    kind = 'order'
    mock = False
    if RAZORPAY_ENABLED and RAZORPAY_SUBS_ENABLED:
        # UPI AUTOPAY: recurring subscription via e-mandate
        try:
            rz_plan_id = await get_or_create_razorpay_plan(body.plan)
            sub = await asyncio.to_thread(lambda: razorpay_client().subscription.create({
                'plan_id': rz_plan_id,
                'total_count': 120 if body.plan == 'monthly' else 10,
                'customer_notify': 1,
                'notes': {'user_id': user['id'], 'plan': body.plan},
            }))
            ref_id = sub['id']
            kind = 'subscription'
        except Exception as e:
            logger.error(f'Razorpay subscription creation failed: {e}')
            raise HTTPException(status_code=502, detail='Could not start Razorpay Autopay checkout.')
    elif RAZORPAY_ENABLED:
        # One-time order (Autopay switches on automatically once Subscriptions is enabled on the account)
        try:
            order = await asyncio.to_thread(lambda: razorpay_client().order.create({
                'amount': amount_paise, 'currency': 'INR', 'payment_capture': 1,
                'receipt': f'ttn-{user["id"][:12]}-{body.plan}'[:40],
                'notes': {'user_id': user['id'], 'plan': body.plan},
            }))
        except Exception as e:
            logger.error(f'Razorpay order creation failed: {e}')
            raise HTTPException(status_code=502, detail='Could not start Razorpay checkout.')
        ref_id = order['id']
    else:
        # MOCKED order — structure mirrors the real integration 1:1
        ref_id = f'order_mock_{uuid.uuid4().hex[:14]}'
        mock = True
    await db.payment_transactions.insert_one({
        'session_id': ref_id, 'user_id': user['id'], 'plan': body.plan,
        'amount': plan['amount_inr'], 'currency': 'inr', 'provider': 'razorpay',
        'kind': kind, 'auto_renew': kind == 'subscription', 'mock': mock,
        'status': 'initiated', 'payment_status': 'pending', 'activated': False,
        'created_at': iso(now_utc()), 'updated_at': iso(now_utc()),
    })
    return {'ok': True, 'mock': mock, 'kind': kind,
            'order_id': ref_id if kind == 'order' else None,
            'subscription_id': ref_id if kind == 'subscription' else None,
            'ref_id': ref_id,
            'amount': amount_paise, 'currency': 'INR',
            'razorpay_key_id': RAZORPAY_KEY_ID or None,
            'name': 'The Trading Narrative',
            'description': f"Premium — {plan['label']} (INR)"}


@api_router.post('/billing/razorpay/verify')
async def razorpay_verify(body: RazorpayVerifyIn, user=Depends(get_current_user)):
    txn = await db.payment_transactions.find_one({'session_id': body.order_id, 'user_id': user['id']})
    if not txn:
        raise HTTPException(status_code=404, detail='Order not found')
    if txn.get('payment_status') == 'paid':
        return {'ok': True, 'already': True}
    if txn.get('mock'):
        # MOCKED: mark paid instantly (no gateway available without keys)
        pass
    elif txn.get('kind') == 'subscription':
        try:
            razorpay_client().utility.verify_subscription_payment_signature({
                'razorpay_subscription_id': body.order_id,
                'razorpay_payment_id': body.payment_id,
                'razorpay_signature': body.signature,
            })
        except Exception:
            raise HTTPException(status_code=400, detail='Payment signature verification failed')
    else:
        try:
            razorpay_client().utility.verify_payment_signature({
                'razorpay_order_id': body.order_id,
                'razorpay_payment_id': body.payment_id,
                'razorpay_signature': body.signature,
            })
        except Exception:
            raise HTTPException(status_code=400, detail='Payment signature verification failed')
    await db.payment_transactions.update_one(
        {'session_id': body.order_id, 'payment_status': {'$ne': 'paid'}},
        {'$set': {'status': 'completed', 'payment_status': 'paid',
                  'razorpay_payment_id': body.payment_id, 'updated_at': iso(now_utc())}},
    )
    txn = await db.payment_transactions.find_one({'session_id': body.order_id})
    await activate_premium_from_transaction(txn)
    return {'ok': True, 'mock': bool(txn.get('mock'))}


@api_router.post('/webhook/razorpay')
async def razorpay_webhook(request: Request):
    if not RAZORPAY_ENABLED:
        return {'status': 'ignored (razorpay not configured)'}
    payload = await request.body()
    signature = request.headers.get('X-Razorpay-Signature', '')
    secret = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    try:
        razorpay_client().utility.verify_webhook_signature(payload.decode(), signature, secret)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid webhook signature')
    import json as _json
    event = _json.loads(payload)
    if event.get('event') == 'payment.captured':
        order_id = event['payload']['payment']['entity'].get('order_id')
        if order_id:
            await db.payment_transactions.update_one(
                {'session_id': order_id, 'payment_status': {'$ne': 'paid'}},
                {'$set': {'status': 'completed', 'payment_status': 'paid', 'updated_at': iso(now_utc())}},
            )
            txn = await db.payment_transactions.find_one({'session_id': order_id})
            if txn:
                await activate_premium_from_transaction(txn)
    return {'status': 'ok'}


# ---------------------- weekly digest ----------------------

def build_digest_html(posts):
    accent = '#1c8570'
    items = ''
    for p in posts:
        items += f"""
        <tr><td style="padding:0 0 28px 0;">
          <img src="{p['cover_image']}" alt="" width="560" style="width:100%;max-width:560px;border-radius:10px;display:block;" />
          <p style="margin:14px 0 4px;font-family:monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{accent};">{p['category_label']}{' &middot; PREMIUM' if p['tier'] == 'premium' else ''}</p>
          <h2 style="margin:0 0 6px;font-family:Georgia,serif;font-size:22px;line-height:1.3;color:#14181f;">
            <a href="{FRONTEND_URL}/post/{p['slug']}" style="color:#14181f;text-decoration:none;">{p['title']}</a>
          </h2>
          <p style="margin:0 0 8px;font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:#555e6b;">{p['excerpt']}</p>
          <a href="{FRONTEND_URL}/post/{p['slug']}" style="font-family:Arial,sans-serif;font-size:13px;color:{accent};font-weight:bold;text-decoration:none;">Read the essay ({p['read_time']} min) &rarr;</a>
        </td></tr>"""
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f4f1ea;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:32px 16px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:14px;padding:36px;">
        <tr><td style="padding-bottom:26px;border-bottom:1px solid #e8e4da;">
          <span style="display:inline-block;width:10px;height:10px;background:{accent};"></span>
          <span style="font-family:Georgia,serif;font-size:22px;font-weight:bold;color:#14181f;">&nbsp;The Trading Narrative</span>
          <p style="margin:10px 0 0;font-family:monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#8a8577;">The week in narratives</p>
        </td></tr>
        <tr><td style="padding:26px 0 6px;">
          <p style="font-family:Arial,sans-serif;font-size:15px;line-height:1.6;color:#3a4150;margin:0 0 24px;">Here's everything published this week &mdash; the sharpest thinking on markets, tech, and living well.</p>
        </td></tr>
        {items}
        <tr><td style="padding-top:8px;border-top:1px solid #e8e4da;">
          <p style="font-family:Arial,sans-serif;font-size:12px;color:#8a8577;margin:16px 0 0;">You're receiving this because you subscribed to The Trading Narrative.<br/>
          <a href="{FRONTEND_URL}" style="color:{accent};">Visit the site</a> &middot; <a href="{FRONTEND_URL}/pricing" style="color:{accent};">Go Premium</a></p>
        </td></tr>
      </table>
    </td></tr></table></body></html>"""


async def get_digest_posts():
    week_ago = iso(now_utc() - timedelta(days=7))
    posts = await db.posts.find({**published_query(), 'published_at': {'$gte': week_ago}}).sort('published_at', -1).to_list(20)
    if not posts:
        posts = await db.posts.find(published_query()).sort('published_at', -1).limit(5).to_list(5)
    return [post_summary(clean(p)) for p in posts]


@api_router.get('/admin/newsletter/digest-preview')
async def digest_preview(admin=Depends(get_admin_user)):
    posts = await get_digest_posts()
    subject = f"The Week in Narratives — {now_utc().strftime('%B %d, %Y')}"
    return {'subject': subject, 'post_count': len(posts), 'posts': posts,
            'html': build_digest_html(posts)}


class DigestSendIn(BaseModel):
    subject: Optional[str] = None


async def do_send_digest(subject: Optional[str] = None, auto: bool = False):
    """Shared digest send used by the admin button and the Friday autosend scheduler."""
    posts = await get_digest_posts()
    if not posts:
        return None
    subject = subject or f"The Week in Narratives — {now_utc().strftime('%B %d, %Y')}"
    subs = await db.newsletter_subscribers.find({'status': 'subscribed'}).to_list(10000)
    titles = ', '.join(p['title'] for p in posts[:5])
    digest_html = build_digest_html(posts)
    for sub in subs:
        await log_email(sub['email'], subject, f'Weekly digest featuring: {titles}', 'digest', html=digest_html)
    issue = {
        'id': str(uuid.uuid4()), 'post_id': None, 'post_title': f'Weekly digest ({len(posts)} essays)',
        'kind': 'digest', 'subject': subject, 'recipients': len(subs),
        'status': ('sent (gmail)' if EMAIL_ENABLED and not EMAIL_LAST_ERROR else 'sent (mocked)') + (' · auto' if auto else ''),
        'auto': auto, 'sent_at': iso(now_utc()),
    }
    await db.newsletter_issues.insert_one(dict(issue))
    return issue


@api_router.post('/admin/newsletter/send-digest')
async def send_digest(body: DigestSendIn, admin=Depends(get_admin_user)):
    issue = await do_send_digest(subject=body.subject, auto=False)
    if not issue:
        raise HTTPException(status_code=400, detail='No published posts to include')
    return clean(issue)


# ---------------------- weekly digest autosend (every Friday) ----------------------

async def digest_autosend_loop():
    """Background loop: sends the weekly digest automatically every Friday (UTC),
    at most once per ISO week, when the admin toggle is on."""
    import asyncio
    while True:
        try:
            cfg = await db.config.find_one({'key': 'digest_autosend'})
            enabled = bool(cfg and cfg.get('value'))
            now = now_utc()
            if enabled and now.weekday() == 4:  # Friday
                week_key = f'{now.isocalendar().year}-W{now.isocalendar().week}'
                sent = await db.config.find_one({'key': 'digest_autosend_last_week'})
                if not sent or sent.get('value') != week_key:
                    issue = await do_send_digest(auto=True)
                    if issue:
                        await db.config.update_one(
                            {'key': 'digest_autosend_last_week'},
                            {'$set': {'value': week_key, 'sent_at': iso(now)}}, upsert=True)
                        logger.info(f'Weekly digest auto-sent to {issue["recipients"]} subscribers ({week_key})')
        except Exception as e:
            logger.warning(f'Digest autosend loop error: {e}')
        await asyncio.sleep(1800)  # check every 30 minutes


@api_router.get('/admin/newsletter/autosend')
async def get_autosend(admin=Depends(get_admin_user)):
    cfg = await db.config.find_one({'key': 'digest_autosend'})
    last = await db.config.find_one({'key': 'digest_autosend_last_week'})
    return {'enabled': bool(cfg and cfg.get('value')),
            'last_auto_send': last.get('sent_at') if last else None}


class AutosendIn(BaseModel):
    enabled: bool


@api_router.post('/admin/newsletter/autosend')
async def set_autosend(body: AutosendIn, admin=Depends(get_admin_user)):
    await db.config.update_one({'key': 'digest_autosend'},
                               {'$set': {'value': body.enabled}}, upsert=True)
    return {'ok': True, 'enabled': body.enabled}


# ---------------------- SEO ----------------------

@api_router.get('/sitemap.xml')
async def sitemap():
    posts = await db.posts.find(published_query()).to_list(1000)
    urls = [FRONTEND_URL, f'{FRONTEND_URL}/archive', f'{FRONTEND_URL}/pricing', f'{FRONTEND_URL}/about']
    urls += [f'{FRONTEND_URL}/category/{slug}' for slug in CATEGORIES]
    urls += [f"{FRONTEND_URL}/post/{p['slug']}" for p in posts]
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    body += ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls)
    body += '</urlset>'
    return Response(content=body, media_type='application/xml')


@api_router.get('/health')
async def health():
    return {'status': 'ok', 'app': 'The Trading Narrative'}


# ---------------------- seed ----------------------

async def seed_database():
    admin_email = 'admin@tradingnarrative.com'
    existing_admin = await db.users.find_one({'email': admin_email})
    if not existing_admin:
        await db.users.insert_one({
            'id': str(uuid.uuid4()), 'email': admin_email, 'name': 'Jordan Hale',
            'password_hash': hash_password('Admin@2025'), 'role': 'admin',
            'created_at': iso(now_utc()),
        })
        logger.info('Seeded admin user')
    count = await db.posts.count_documents({})
    if count == 0:
        base = now_utc()
        for idx, sp in enumerate(SAMPLE_POSTS):
            published = base - timedelta(days=idx * 2 + 1, hours=idx)
            post = {
                'id': str(uuid.uuid4()), 'slug': slugify(sp['title']), 'title': sp['title'],
                'excerpt': sp['excerpt'], 'category': sp['category'], 'tier': sp['tier'],
                'cover_image': sp['cover_image'], 'content_blocks': sp['content_blocks'],
                'tags': sp.get('tags', []),
                'featured': sp.get('featured', False), 'status': 'published', 'publish_at': None,
                'published_at': iso(published), 'author': AUTHOR,
                'read_time': read_time(sp['content_blocks']),
                'views': random.randint(120, 2400),
                'created_at': iso(published), 'updated_at': iso(published),
            }
            await db.posts.insert_one(post)
        logger.info(f'Seeded {len(SAMPLE_POSTS)} posts')
    # backfill tags on already-seeded posts
    for sp in SAMPLE_POSTS:
        if sp.get('tags'):
            await db.posts.update_one(
                {'slug': slugify(sp['title']), 'tags': {'$exists': False}},
                {'$set': {'tags': sp['tags']}},
            )


@app.on_event('startup')
async def startup():
    import asyncio
    await seed_database()
    await probe_razorpay_subscriptions()
    asyncio.create_task(digest_autosend_loop())


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('shutdown')
async def shutdown_db_client():
    client.close()
