"""The Trading Narrative — FastAPI entrypoint.

App assembly only: routers live in /routers, shared logic in /services,
config/db/security/schemas/utils are top-level modules.
"""
import os
import uuid
import asyncio
from datetime import timedelta

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import logger, EARLY_SUPPORTER_LIMIT  # loads .env first
from db import client, db
from utils import now_utc, iso, slugify, read_time
from security import hash_password
from seed_data import SAMPLE_POSTS, REAL_POSTS, AUTHOR
from services.razorpay_service import probe_razorpay_subscriptions
from services.digest_service import digest_autosend_loop, briefing_reminder_loop, briefing_autosend_loop
from services.tts_service import warm_all_narrations

from routers import auth, posts, billing, razorpay_routes, newsletter, analytics, community, admin, highlights, sync, ai

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
                # Demo essays seed as DRAFTS: fresh deployments start with a clean public
                # site and the owner publishes real content (or drafts) from the admin studio.
                'featured': sp.get('featured', False), 'status': 'draft', 'publish_at': None,
                'published_at': iso(published), 'author': AUTHOR,
                'read_time': read_time(sp['content_blocks']),
                'views': 0,
                'created_at': iso(published), 'updated_at': iso(published),
            }
            await db.posts.insert_one(post)
        logger.info(f'Seeded {len(SAMPLE_POSTS)} sample posts as drafts')
    # REAL site content: always ensure the author's actual articles exist (matched by
    # slug) — hardcoded in seed_data.py so a DB reset or fresh deployment never loses them.
    for rp in REAL_POSTS:
        if await db.posts.find_one({'slug': rp['slug']}):
            continue
        published_at = rp.get('published_at') or iso(now_utc())
        await db.posts.insert_one({
            'id': str(uuid.uuid4()), 'slug': rp['slug'], 'title': rp['title'],
            'excerpt': rp['excerpt'], 'category': rp['category'], 'tier': rp['tier'],
            'cover_image': rp['cover_image'], 'content_blocks': rp['content_blocks'],
            'tags': rp.get('tags', []), 'featured': rp.get('featured', False),
            'status': 'published', 'publish_at': None, 'edition': rp.get('edition'),
            'published_at': published_at, 'author': AUTHOR,
            'read_time': read_time(rp['content_blocks']), 'views': 0,
            'created_at': published_at, 'updated_at': published_at,
        })
        logger.info(f"Restored real article from seed: {rp['title'][:60]}")
    # backfill tags on already-seeded posts
    for sp in SAMPLE_POSTS:
        if sp.get('tags'):
            await db.posts.update_one(
                {'slug': slugify(sp['title']), 'tags': {'$exists': False}},
                {'$set': {'tags': sp['tags']}},
            )
    # Brand consistency: every essay is authored by Anish Pujari.
    # Self-heals any legacy author values (runs on preview and production alike).
    res = await db.posts.update_many(
        {'author.name': {'$ne': AUTHOR['name']}}, {'$set': {'author': AUTHOR}})
    if res.modified_count:
        logger.info(f"Normalized author to '{AUTHOR['name']}' on {res.modified_count} posts")
    # One-time cleanup: unpublish demo/sample essays so ElevenLabs credits are spent
    # only on real writing (runs once per DB; the admin can republish any of them later).
    if not await db.migrations.find_one({'key': 'unpublish_demo_posts_v1'}):
        demo_slugs = [slugify(sp['title']) for sp in SAMPLE_POSTS]
        res = await db.posts.update_many(
            {'slug': {'$in': demo_slugs}, 'status': 'published'},
            {'$set': {'status': 'draft', 'updated_at': iso(now_utc())}})
        await db.migrations.insert_one({'key': 'unpublish_demo_posts_v1',
                                        'applied_at': iso(now_utc()),
                                        'unpublished': res.modified_count})
        if res.modified_count:
            logger.info(f'One-time cleanup: unpublished {res.modified_count} demo essays')

    # LAUNCH PROMO: backfill early-supporter slots — the oldest registered readers claim
    # the first EARLY_SUPPORTER_LIMIT spots (idempotent; tops up until 50 are marked).
    flagged = await db.users.count_documents({'early_supporter': True})
    if flagged < EARLY_SUPPORTER_LIMIT:
        candidates = await db.users.find({'early_supporter': {'$ne': True}}) \
            .sort('created_at', 1).limit(EARLY_SUPPORTER_LIMIT - flagged).to_list(EARLY_SUPPORTER_LIMIT)
        if candidates:
            await db.users.update_many({'id': {'$in': [u['id'] for u in candidates]}},
                                       {'$set': {'early_supporter': True}})
            logger.info(f'Early-supporter promo: marked {len(candidates)} readers (total ≤ {EARLY_SUPPORTER_LIMIT})')

    # PHASE 38 CONTENT STRATEGY (one-time): briefings free through Edition #6;
    # Tech & AI, Delivery & Systems and Personal Growth essays go premium.
    if not await db.migrations.find_one({'key': 'phase38_tier_strategy_v1'}):
        r1 = await db.posts.update_many(
            {'edition': {'$ne': None, '$lte': 6}, 'tier': {'$ne': 'free'}},
            {'$set': {'tier': 'free', 'updated_at': iso(now_utc())}})
        r2 = await db.posts.update_many(
            {'category': {'$in': ['tech-business', 'delivery', 'lifestyle']},
             'edition': None, 'status': 'published', 'tier': {'$ne': 'premium'}},
            {'$set': {'tier': 'premium', 'updated_at': iso(now_utc())}})
        await db.migrations.insert_one({'key': 'phase38_tier_strategy_v1',
                                        'applied_at': iso(now_utc()),
                                        'briefings_freed': r1.modified_count,
                                        'essays_premiumed': r2.modified_count})
        logger.info(f'Phase 38 tiers: {r1.modified_count} briefings -> free, {r2.modified_count} essays -> premium')


@app.on_event('startup')
async def startup():
    await seed_database()
    await probe_razorpay_subscriptions()
    asyncio.create_task(digest_autosend_loop())
    asyncio.create_task(briefing_reminder_loop())
    asyncio.create_task(briefing_autosend_loop())
    asyncio.create_task(warm_all_narrations())


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(billing.router)
app.include_router(razorpay_routes.router)
app.include_router(newsletter.router)
app.include_router(analytics.router)
app.include_router(community.router)
app.include_router(admin.router)
app.include_router(highlights.router)
app.include_router(sync.router)
app.include_router(ai.router)

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
