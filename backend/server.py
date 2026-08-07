"""The Trading Narrative — FastAPI entrypoint.

App assembly only: routers live in /routers, shared logic in /services,
config/db/security/schemas/utils are top-level modules.
"""
import os
import uuid
import random
import asyncio
from datetime import timedelta

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import logger  # loads .env first
from db import client, db
from utils import now_utc, iso, slugify, read_time
from security import hash_password
from seed_data import SAMPLE_POSTS, AUTHOR
from services.razorpay_service import probe_razorpay_subscriptions
from services.digest_service import digest_autosend_loop, briefing_reminder_loop

from routers import auth, posts, billing, razorpay_routes, newsletter, analytics, community, admin, highlights

app = FastAPI(title='The Trading Narrative API')


# ---------------------- seed ----------------------

async def seed_database():
    admin_email = 'admin@tradingnarrative.com'
    existing_admin = await db.users.find_one({'email': admin_email})
    if not existing_admin:
        await db.users.insert_one({
            'id': str(uuid.uuid4()), 'email': admin_email, 'name': 'Anish Pujari',
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
    await seed_database()
    await probe_razorpay_subscriptions()
    asyncio.create_task(digest_autosend_loop())
    asyncio.create_task(briefing_reminder_loop())


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(billing.router)
app.include_router(razorpay_routes.router)
app.include_router(newsletter.router)
app.include_router(analytics.router)
app.include_router(community.router)
app.include_router(admin.router)
app.include_router(highlights.router)

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
