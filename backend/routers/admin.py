"""Admin routes: post CRUD, subscribers, issues, stats, email status/test/logs."""
import asyncio
import base64
import uuid
from datetime import timedelta

from bson import Binary
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from config import (CATEGORIES, FRONTEND_URL, EMAIL_ENABLED, EMAIL_FROM_NAME,
                    EMAIL_REPLY_TO, GMAIL_SMTP_USER, TTS_ENABLED, TTS_VOICES)
from db import db
from utils import now_utc, iso, clean, slugify, read_time, post_summary, published_query
from security import get_admin_user
from schemas import PostIn, IssueIn
from seed_data import AUTHOR
from services import emailer
from services.emailer import log_email

router = APIRouter(prefix='/api')


@router.get('/admin/posts')
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


@router.get('/admin/posts/{post_id}')
async def admin_get_post(post_id: str, admin=Depends(get_admin_user)):
    post = await db.posts.find_one({'id': post_id})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    return clean(post)


@router.post('/admin/posts')
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
        'status': body.status, 'publish_at': body.publish_at, 'edition': body.edition,
        'published_at': iso(now_utc()) if body.status == 'published' else (body.publish_at or iso(now_utc())),
        'author': AUTHOR, 'read_time': read_time(body.content_blocks), 'views': 0,
        'created_at': iso(now_utc()), 'updated_at': iso(now_utc()),
    }
    await db.posts.insert_one(dict(post))
    return clean(post)


@router.put('/admin/posts/{post_id}')
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
        'edition': body.edition,
        'read_time': read_time(body.content_blocks), 'updated_at': iso(now_utc()),
    }
    if body.status == 'published' and post.get('status') != 'published':
        updates['published_at'] = iso(now_utc())
    await db.posts.update_one({'id': post_id}, {'$set': updates})
    updated = await db.posts.find_one({'id': post_id})
    if updated.get('status') == 'published':
        # content changed (post_version bumps) — regenerate narration ahead of the next listener
        from services.tts_service import warm_post_audio
        asyncio.create_task(warm_post_audio(dict(updated)))
    return clean(updated)


@router.delete('/admin/posts/{post_id}')
async def admin_delete_post(post_id: str, admin=Depends(get_admin_user)):
    result = await db.posts.delete_one({'id': post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Post not found')
    return {'ok': True}


@router.get('/admin/newsletter/subscribers')
async def admin_subscribers(admin=Depends(get_admin_user)):
    subs = await db.newsletter_subscribers.find({}).sort('created_at', -1).to_list(1000)
    return {'subscribers': [clean(s) for s in subs], 'total': len(subs)}


@router.post('/admin/newsletter/issues')
async def admin_send_issue(body: IssueIn, admin=Depends(get_admin_user)):
    post = await db.posts.find_one({'id': body.post_id})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    subs = await db.newsletter_subscribers.find({'status': 'subscribed'}).to_list(10000)
    # respect per-category email preferences (missing prefs = all categories)
    subs = [x for x in subs if post['category'] in x.get('categories', list(CATEGORIES.keys()))]
    subject = body.subject or f"New on The Trading Narrative: {post['title']}"
    post_url = f"{FRONTEND_URL}/post/{post['slug']}"
    for s in subs:
        await log_email(s['email'], subject, f"{post.get('excerpt', '')}\n\nRead: {post_url}", 'issue',
                        html=f"<h2 style='font-family:Georgia,serif'>{post['title']}</h2><p>{post.get('excerpt', '')}</p><p><a href='{post_url}'>Read the full essay →</a></p>")
    issue = {
        'id': str(uuid.uuid4()), 'post_id': post['id'], 'post_title': post['title'],
        'subject': subject, 'recipients': len(subs),
        'status': 'sent (gmail)' if EMAIL_ENABLED and not emailer.EMAIL_LAST_ERROR else 'sent (mocked)',
        'sent_at': iso(now_utc()),
    }
    await db.newsletter_issues.insert_one(dict(issue))
    return clean(issue)


@router.get('/admin/newsletter/issues')
async def admin_issues(admin=Depends(get_admin_user)):
    issues = await db.newsletter_issues.find({}).sort('sent_at', -1).to_list(200)
    return {'issues': [clean(i) for i in issues]}


# ---------------------- narration status panel ----------------------

class AudioCacheImportIn(BaseModel):
    post_slug: str = Field(min_length=1)
    voice: str
    scope: str
    audio_b64: str = Field(min_length=1)
    chars: int = 0


@router.post('/admin/audio-cache/import')
async def import_audio_cache(body: AudioCacheImportIn, admin=Depends(get_admin_user)):
    """Accept a pre-generated narration pushed from another environment (preview -> production).
    Stored against THIS environment's post version so it is served as a fresh cache hit."""
    if body.voice not in TTS_VOICES or body.scope not in ('full', 'preview'):
        raise HTTPException(status_code=400, detail='Invalid voice or scope')
    post = await db.posts.find_one({'slug': body.post_slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail=f'Post {body.post_slug} is not published here')
    try:
        audio = base64.b64decode(body.audio_b64)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid audio payload')
    if not audio or len(audio) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='Audio payload empty or too large')
    key = {'post_slug': body.post_slug, 'voice': body.voice, 'scope': body.scope}
    await db.audio_cache.update_one(key, {'$set': {
        **key,
        'post_version': post.get('updated_at') or post.get('published_at') or '',
        'audio': Binary(audio), 'bytes': len(audio), 'chars': body.chars,
        'created_at': iso(now_utc()),
    }}, upsert=True)
    logger_bytes = len(audio)
    return {'ok': True, 'bytes': logger_bytes}


@router.get('/admin/narrations')
async def admin_narrations(admin=Depends(get_admin_user)):
    """Per-essay narration cache status + live ElevenLabs credit balance."""
    from services.tts_service import get_credits, WARMUP_STATE, DEFAULT_WARM_VOICE
    credits = await get_credits()
    posts = await db.posts.find(published_query()).sort('published_at', -1).to_list(500)
    cache_docs = await db.audio_cache.find({'voice': DEFAULT_WARM_VOICE}, {'audio': 0}).to_list(1000)
    by_slug = {}
    for c in cache_docs:
        by_slug.setdefault(c['post_slug'], {})[c.get('scope', 'full')] = c
    essays = []
    for p in posts:
        version = p.get('updated_at') or p.get('published_at') or ''
        entries = by_slug.get(p['slug'], {})
        needed = ['full'] + (['preview'] if p.get('tier') == 'premium' else [])
        ready_scopes, total_bytes, cached = [], 0, True
        for s in needed:
            c = entries.get(s)
            if c and c.get('post_version') == version:
                ready_scopes.append(s)
                total_bytes += c.get('bytes', 0)
            else:
                cached = False
        ms = p.get('listen_milestones', {}) or {}
        listens = p.get('listens', 0)
        finished = ms.get('100', 0)
        essays.append({'slug': p['slug'], 'title': p['title'], 'tier': p.get('tier', 'free'),
                       'cached': cached, 'scopes': ready_scopes, 'bytes': total_bytes,
                       'listens': listens,
                       'milestones': {'25': ms.get('25', 0), '50': ms.get('50', 0),
                                      '75': ms.get('75', 0), '100': finished},
                       'completion': round(100 * min(finished, listens) / listens) if listens else None})
    return {'enabled': TTS_ENABLED, 'warming': WARMUP_STATE['running'], 'credits': credits,
            'cached_count': sum(1 for e in essays if e['cached']), 'total': len(essays),
            'essays': essays}


@router.post('/admin/narrations/warm')
async def admin_warm_narrations(admin=Depends(get_admin_user)):
    """Kick off background pre-generation of every missing narration (skips cached ones)."""
    if not TTS_ENABLED:
        raise HTTPException(status_code=503, detail='Narration is not configured')
    from services.tts_service import warm_all_narrations, WARMUP_STATE
    if WARMUP_STATE['running']:
        return {'ok': True, 'started': False, 'message': 'A warmup run is already in progress.'}
    asyncio.create_task(warm_all_narrations(initial_delay=0))
    return {'ok': True, 'started': True,
            'message': 'Warmup started — missing narrations are being generated in the background.'}


@router.get('/admin/analytics/stats')
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
    listens_agg = await db.posts.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': {'$ifNull': ['$listens', 0]}}}},
    ]).to_list(1)
    listens = listens_agg[0]['total'] if listens_agg else 0
    listens_7d = await db.analytics.count_documents({'event': 'narration_listen', 'created_at': {'$gte': week_ago}})
    return {
        'pageviews': pageviews, 'pageviews_7d': pageviews_7d,
        'listens': listens, 'listens_7d': listens_7d,
        'newsletter_subscribers': nl_subs, 'users': users,
        'premium_subscribers': premium, 'checkouts': checkouts,
        'subscribe_cta_clicks': cta_clicks,
        'top_posts': [{'title': p['title'], 'slug': p['slug'], 'views': p.get('views', 0),
                       'listens': p.get('listens', 0)} for p in top_posts],
    }


@router.get('/admin/email/status')
async def email_status(admin=Depends(get_admin_user)):
    last_error = emailer.EMAIL_LAST_ERROR
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


@router.post('/admin/email/test')
async def email_test(admin=Depends(get_admin_user)):
    entry = await log_email(GMAIL_SMTP_USER or admin['email'],
                            'Test email — The Trading Narrative',
                            'If you are reading this, real email sending works.',
                            'test',
                            html='<p>If you are reading this, <strong>real email sending works</strong>. — The Trading Narrative</p>')
    return {'status': entry['status'], 'to': entry['to'], 'last_error': emailer.EMAIL_LAST_ERROR}


@router.get('/admin/email-logs')
async def admin_email_logs(admin=Depends(get_admin_user), limit: int = Query(50, le=200)):
    logs = await db.email_logs.find({}).sort('sent_at', -1).limit(limit).to_list(limit)
    return {'logs': [clean(l) for l in logs]}
