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

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret')
JWT_ALGO = 'HS256'
JWT_EXPIRY_DAYS = 30
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
MOCK_BILLING = os.environ.get('MOCK_BILLING', 'true').lower() == 'true'

PLANS = {
    'monthly': {'id': 'monthly', 'label': 'Monthly', 'amount': 8.00, 'currency': 'usd', 'interval': 'month'},
    'annual': {'id': 'annual', 'label': 'Annual', 'amount': 80.00, 'currency': 'usd', 'interval': 'year'},
}

CATEGORIES = {
    'tech-business': 'Tech & Business',
    'finance': 'Finance',
    'lifestyle': 'Lifestyle',
    'travel': 'Travel',
}

PREVIEW_BLOCKS = 3  # paragraphs shown to non-premium users on premium posts

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
        'author': p.get('author', AUTHOR), 'published_at': p.get('published_at'),
        'status': p.get('status', 'published'), 'views': p.get('views', 0),
    }


def published_query():
    now = iso(now_utc())
    return {'$or': [
        {'status': 'published'},
        {'status': 'scheduled', 'publish_at': {'$lte': now}},
    ]}


async def log_email(to: str, subject: str, body: str, kind: str):
    """MOCKED email provider adapter. Swap with Mailchimp/ConvertKit/Resend later."""
    entry = {
        'id': str(uuid.uuid4()), 'to': to, 'subject': subject, 'body': body,
        'kind': kind, 'provider': os.environ.get('NEWSLETTER_PROVIDER', 'mock'),
        'sent_at': iso(now_utc()), 'status': 'sent (mocked)',
    }
    await db.email_logs.insert_one(dict(entry))
    logger.info(f"[MOCK EMAIL] to={to} subject='{subject}' kind={kind}")
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
                     limit: int = Query(50, le=100), skip: int = 0):
    query = published_query()
    if category:
        query['category'] = category
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


# ---------------------- billing (MOCKED - Stripe-ready) ----------------------

@api_router.get('/billing/config')
async def billing_config():
    return {'mock_mode': MOCK_BILLING, 'plans': list(PLANS.values())}


@api_router.post('/billing/checkout')
async def checkout(body: CheckoutIn, user=Depends(get_current_user)):
    if body.plan not in PLANS:
        raise HTTPException(status_code=400, detail='Invalid plan')
    existing = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail='You already have an active subscription')
    if not MOCK_BILLING:
        # TODO: real Stripe checkout session creation goes here (STRIPE_SECRET_KEY)
        raise HTTPException(status_code=501, detail='Stripe not configured yet')
    plan = PLANS[body.plan]
    period_days = 365 if body.plan == 'annual' else 30
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
    await db.analytics.insert_one({'id': str(uuid.uuid4()), 'event': 'checkout_complete',
                                   'path': '/pricing', 'meta': {'plan': body.plan},
                                   'user_id': user['id'], 'created_at': iso(now_utc())})
    await log_email(user['email'], 'Welcome to Premium — The Trading Narrative',
                    f"Your {plan['label']} subscription is active. Enjoy full access.", 'premium_welcome')
    return {'ok': True, 'subscription': clean(sub), 'invoice': clean(invoice)}


@api_router.post('/billing/cancel')
async def cancel_subscription(user=Depends(get_current_user)):
    sub = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if not sub:
        raise HTTPException(status_code=400, detail='No active subscription')
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


# ---------------------- analytics ----------------------

@api_router.post('/analytics/track')
async def track(body: TrackIn, user=Depends(get_optional_user)):
    await db.analytics.insert_one({
        'id': str(uuid.uuid4()), 'event': body.event, 'path': body.path,
        'meta': body.meta, 'user_id': user['id'] if user else None,
        'created_at': iso(now_utc()),
    })
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
        'content_blocks': body.content_blocks, 'featured': body.featured,
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


@api_router.get('/admin/email-logs')
async def admin_email_logs(admin=Depends(get_admin_user), limit: int = Query(50, le=200)):
    logs = await db.email_logs.find({}).sort('sent_at', -1).limit(limit).to_list(limit)
    return {'logs': [clean(l) for l in logs]}


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
                'featured': sp.get('featured', False), 'status': 'published', 'publish_at': None,
                'published_at': iso(published), 'author': AUTHOR,
                'read_time': read_time(sp['content_blocks']),
                'views': random.randint(120, 2400),
                'created_at': iso(published), 'updated_at': iso(published),
            }
            await db.posts.insert_one(post)
        logger.info(f'Seeded {len(SAMPLE_POSTS)} posts')


@app.on_event('startup')
async def startup():
    await seed_database()


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
