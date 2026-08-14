"""Public content routes: categories, posts, comments, notifications, bookmarks,
recommendations, briefings, sitemap, health."""
import hashlib
import re
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import Response, HTMLResponse

from config import (CATEGORIES, PREVIEW_BLOCKS, FRONTEND_URL, SERIES, TTS_ENABLED, TTS_VOICES,
                    AUDIO_CLIP_BYTES, AUDIO_UNLOCK_PRICE_USD, AUDIO_UNLOCK_PRICE_INR,
                    EARLY_FREE_POSTS, METER_FREE_READS, METER_COOKIE,
                    METER_COOKIE_DAYS, PREVIEW_WORDS, logger)
from db import db
from utils import (now_utc, iso, clean, post_summary, published_query,
                   has_free_audio, owns_audio, premium_audio_only, meta_description)
from security import get_optional_user, get_current_user, is_entitled
from schemas import CommentIn, BookmarkToggleIn, AudioProgressIn

router = APIRouter(prefix='/api')


# ---------------------- metered access helpers ----------------------

def _meter_key(request: Request) -> str:
    """Server-side meter fallback key: hashed IP+UA (survives cookie clearing).
    No raw IPs are stored — only the hash."""
    ip = (request.headers.get('x-forwarded-for') or (request.client.host if request.client else '')).split(',')[0].strip()
    ua = request.headers.get('user-agent', '')
    return hashlib.sha256(f'{ip}|{ua}'.encode()).hexdigest()


def _cookie_slugs(request: Request) -> set:
    raw = request.cookies.get(METER_COOKIE, '')
    return {s for s in raw.split('|') if s}


def preview_slice(blocks):
    """Locked-essay preview: first ~PREVIEW_WORDS words or first 2 blocks, whichever is shorter."""
    out, words = [], 0
    for b in blocks[:2]:
        take = b.split()
        if words + len(take) > PREVIEW_WORDS:
            out.append(' '.join(take[:max(20, PREVIEW_WORDS - words)]) + '…')
            break
        out.append(b)
        words += len(take)
    return out


async def _latest_edition_slugs(n: int = 3) -> set:
    docs = await db.posts.find({**published_query(), 'edition': {'$ne': None}}, {'slug': 1}) \
        .sort('edition', -1).limit(n).to_list(n)
    return {d['slug'] for d in docs}


@router.get('/categories')
async def get_categories():
    result = []
    for slug, label in CATEGORIES.items():
        count = await db.posts.count_documents({'category': slug, **published_query()})
        result.append({'slug': slug, 'label': label, 'count': count})
    return result


@router.get('/posts')
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


@router.get('/posts/{slug}')
async def get_post(slug: str, request: Request, response: Response, user=Depends(get_optional_user)):
    post = await db.posts.find_one({'slug': slug, **published_query()})
    early_access = False
    if not post and user:
        # EARLY ACCESS (Lounge perk): premium members + admins can read scheduled drafts before publish
        scheduled = await db.posts.find_one({'slug': slug, 'status': 'scheduled'})
        if scheduled and (user.get('role') == 'admin' or await is_entitled(user)):
            post = scheduled
            early_access = True
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    clean(post)
    entitled = await is_entitled(user)
    blocks = post.get('content_blocks', [])
    total_blocks = len(blocks)

    # ---- ACCESS RULES (server-side; identical HTML for crawlers and humans — no cloaking) ----
    # Hard-locked for non-entitled (never metered): premium tier, 'lounge'-tagged deep dives,
    # and the 3 most recent editions. Free-tier essays are metered for anonymous visitors.
    lock_reason = None
    hard_locked = post.get('tier') == 'premium' or 'lounge' in (post.get('tags') or [])
    if not hard_locked and post.get('edition') and post.get('tier') != 'free':
        hard_locked = post['slug'] in await _latest_edition_slugs(3)

    is_locked = hard_locked and not entitled
    early_unlock = False
    meter = None

    if is_locked and user and user.get('early_supporter'):
        # LAUNCH PROMO: early supporters (first 50 readers) can read the first 5 published essays free
        early_docs = await db.posts.find(published_query(), {'slug': 1}) \
            .sort('published_at', 1).limit(EARLY_FREE_POSTS).to_list(EARLY_FREE_POSTS)
        if post['slug'] in {d['slug'] for d in early_docs}:
            is_locked = False
            early_unlock = True

    if is_locked:
        lock_reason = 'premium'
        # SERVER-SIDE PAYWALL previews: signed-in readers get the classic 3-block preview;
        # anonymous readers get the SEO preview (~250 words / 2 blocks)
        blocks = blocks[:PREVIEW_BLOCKS] if user else preview_slice(blocks)
    elif user is None:
        # METER: anonymous visitors may read METER_FREE_READS complete free-tier essays.
        # Tracked in a first-party cookie + a hashed IP+UA server record (union of both).
        key = _meter_key(request)
        record = await db.meter_reads.find_one({'key': key}) or {}
        seen = _cookie_slugs(request) | set(record.get('slugs', []))
        if post['slug'] in seen:
            granted = True  # re-reads never consume quota
        elif len(seen) < METER_FREE_READS:
            granted = True
            seen = seen | {post['slug']}
            await db.meter_reads.update_one(
                {'key': key},
                {'$addToSet': {'slugs': post['slug']}, '$set': {'updated_at': iso(now_utc())}},
                upsert=True)
            response.set_cookie(
                METER_COOKIE, '|'.join(sorted(seen)), max_age=METER_COOKIE_DAYS * 86400,
                samesite='lax', secure=True, httponly=False, path='/')
        else:
            granted = False
        used = min(len(seen), METER_FREE_READS)
        meter = {'limit': METER_FREE_READS, 'used': used,
                 'remaining': max(0, METER_FREE_READS - used), 'granted': granted}
        if not granted:
            is_locked = True
            lock_reason = 'meter'
            blocks = preview_slice(blocks)
    # related posts: score by shared tags first, category as fallback signal
    tags = set(post.get('tags', []))
    rel_filter = {'$or': [{'tags': {'$in': list(tags)}}, {'category': post['category']}]} if tags \
        else {'category': post['category']}
    candidates = await db.posts.find(
        {'$and': [published_query(), {'slug': {'$ne': slug}}, rel_filter]}
    ).sort('published_at', -1).to_list(50)

    def _rel_score(p):
        shared = len(tags & set(p.get('tags', [])))
        same_cat = 1 if p['category'] == post['category'] else 0
        return (shared * 2 + same_cat, p.get('published_at') or '')

    related = [post_summary(clean(r)) for r in sorted(candidates, key=_rel_score, reverse=True)[:3]]
    # increment views (fire & forget semantics)
    await db.posts.update_one({'slug': slug}, {'$inc': {'views': 1}})
    result = post_summary(post)
    # editorial series membership (e.g. Trading Operations)
    series_info = next(({'slug': s['slug'], 'title': s['title']}
                        for s in SERIES.values() if slug in s['post_slugs']), None)
    result.update({
        'content_blocks': blocks,
        'is_locked': is_locked,
        'lock_reason': lock_reason,
        'meter': meter,
        'early_unlock': early_unlock,
        'early_access': early_access,
        'publish_at': post.get('publish_at') if early_access else None,
        'total_blocks': total_blocks,
        'shown_blocks': len(blocks),
        'related': related,
        'series': series_info,
    })
    return result


# ---------------------- comments (premium members) ----------------------

@router.get('/posts/{slug}/comments')
async def list_comments(slug: str):
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    comments = await db.comments.find({'post_id': post['id']}).sort('created_at', -1).to_list(500)
    return {'comments': [clean(c) for c in comments], 'total': len(comments)}


@router.post('/posts/{slug}/comments')
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

@router.get('/notifications')
async def get_notifications(user=Depends(get_current_user)):
    notifs = await db.notifications.find({'user_id': user['id']}).sort('created_at', -1).limit(50).to_list(50)
    unread = await db.notifications.count_documents({'user_id': user['id'], 'read': False})
    return {'notifications': [clean(n) for n in notifs], 'unread': unread}


@router.post('/notifications/mark-read')
async def mark_notifications_read(user=Depends(get_current_user)):
    await db.notifications.update_many({'user_id': user['id'], 'read': False}, {'$set': {'read': True}})
    return {'ok': True}


@router.delete('/comments/{comment_id}')
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

@router.get('/bookmarks')
async def get_bookmarks(user=Depends(get_current_user)):
    marks = await db.bookmarks.find({'user_id': user['id']}).sort('created_at', -1).to_list(500)
    post_ids = [m['post_id'] for m in marks]
    posts_map = {}
    if post_ids:
        posts = await db.posts.find({'id': {'$in': post_ids}, **published_query()}).to_list(500)
        posts_map = {p['id']: post_summary(clean(p)) for p in posts}
    ordered = [posts_map[pid] for pid in post_ids if pid in posts_map]
    return {'posts': ordered, 'post_ids': post_ids}


@router.post('/bookmarks/toggle')
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

@router.get('/recommendations')
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


# ---------------------- briefings series ----------------------

@router.get('/briefings')
async def list_briefings():
    """All published weekly briefings (posts with an edition number), newest edition first."""
    posts = await db.posts.find({**published_query(), 'edition': {'$ne': None}}).sort('edition', -1).to_list(200)
    return {'briefings': [post_summary(p) for p in posts]}


# ---------------------- editorial series ----------------------

@router.get('/series')
async def list_series():
    out = []
    for s in SERIES.values():
        count = await db.posts.count_documents({'slug': {'$in': s['post_slugs']}, **published_query()})
        out.append({'slug': s['slug'], 'title': s['title'], 'description': s['description'], 'count': count})
    return {'series': out}


@router.get('/series/{series_slug}')
async def get_series(series_slug: str):
    s = SERIES.get(series_slug)
    if not s:
        raise HTTPException(status_code=404, detail='Series not found')
    posts = await db.posts.find({'slug': {'$in': s['post_slugs']}, **published_query()}).to_list(50)
    by_slug = {p['slug']: post_summary(clean(p)) for p in posts}
    ordered = [by_slug[sl] for sl in s['post_slugs'] if sl in by_slug]
    return {'slug': s['slug'], 'title': s['title'], 'description': s['description'],
            'count': len(ordered), 'posts': ordered}


# ---------------------- social share (OG unfurl) ----------------------

@router.get('/og/{slug}.png')
async def og_card(slug: str):
    """Branded 1200x630 Open Graph share card for an essay (Pillow, disk-cached).
    Used as og:image / twitter:image so links unfurl with a consistent branded
    preview on LinkedIn, X, WhatsApp and Telegram."""
    from services.og_service import get_or_render_card
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    data = await get_or_render_card(post)
    return Response(content=data, media_type='image/png',
                    headers={'Cache-Control': 'public, max-age=86400'})


@router.get('/share/{slug}')
async def share_page(slug: str):
    """Crawler-readable HTML with per-essay Open Graph / Twitter cards.
    LinkedIn & X bots read the meta tags; humans are redirected to the article."""
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    title = post['title'].replace('"', '&quot;')
    # Dynamic per-essay meta description derived from the article content
    desc = meta_description(post).replace('"', '&quot;')[:300]
    # Branded OG card (title + wordmark) so shares look consistent on LinkedIn/X;
    # JSON-LD keeps the real cover photo, which Google prefers for articles.
    image = f'{FRONTEND_URL}/api/og/{slug}.png'
    cover = post.get('cover_image', '')
    canonical = f'{FRONTEND_URL}/post/{slug}'
    # Paywall structured data (Google-compliant paywall signalling — no cloaking)
    import json as _json
    locked = post.get('tier') == 'premium' or 'lounge' in (post.get('tags') or [])
    ld = {
        '@context': 'https://schema.org', '@type': 'NewsArticle',
        'headline': post['title'],
        'datePublished': post.get('published_at', ''),
        'dateModified': post.get('updated_at') or post.get('published_at', ''),
        'author': {'@type': 'Person', 'name': 'Anish Pujari'},
        'publisher': {'@type': 'Organization', 'name': 'The Trading Narrative',
                      'logo': {'@type': 'ImageObject', 'url': f'{FRONTEND_URL}/logo.png'}},
        'description': meta_description(post),
        'keywords': ', '.join(post.get('tags', [])),
        'mainEntityOfPage': canonical,
        'image': cover or image,
        'isAccessibleForFree': not locked,
    }
    if locked:
        ld['hasPart'] = {'@type': 'WebPageElement', 'isAccessibleForFree': False,
                         'cssSelector': '.paywalled-content'}
    ld_script = f'<script type="application/ld+json">{_json.dumps(ld)}</script>'
    html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8">
<title>{title} · The Trading Narrative</title>
{ld_script}
<meta property="og:site_name" content="The Trading Narrative">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/png">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{image}">
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta http-equiv="refresh" content="0;url=/post/{slug}">
<script>window.location.replace('/post/{slug}');</script>
</head><body>
<p>Redirecting to <a href="/post/{slug}">{title}</a>&hellip;</p>
</body></html>"""
    return HTMLResponse(content=html)


# ---------------------- essay audio narration (ElevenLabs) ----------------------

@router.get('/posts/{slug}/audio/access')
async def post_audio_access(slug: str, user=Depends(get_optional_user)):
    """Narration entitlement for this reader on this essay.
    NARRATION POLICY: premium = full everywhere; newsletter editions + shipping industry
    essays are free full audio for signed-in readers; every other essay narration is a
    20s preview unless bought a la carte (₹45 / $0.50)."""
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    premium = await is_entitled(user) if user else False
    free_audio = has_free_audio(post)
    purchased = owns_audio(user, slug)
    full = premium or free_audio or purchased
    # PREMIUM PILLARS (Tech & AI / Personal Growth / Delivery & Systems):
    # narration is exclusive to Premium members — no player, no a la carte unlock
    hidden = premium_audio_only(post) and not premium
    return {
        'enabled': TTS_ENABLED,
        'requires_signin': not bool(user),
        'is_premium': premium,
        'free_audio': free_audio,
        'purchased': purchased,
        'hidden': hidden,
        'scope': 'full' if full else 'clip',
        'unlockable': not full and not hidden,
        'price_inr': AUDIO_UNLOCK_PRICE_INR,
        'price_usd': AUDIO_UNLOCK_PRICE_USD,
    }


@router.get('/posts/{slug}/audio')
async def post_audio(slug: str, voice: str = 'male', user=Depends(get_optional_user)):
    if not TTS_ENABLED:
        raise HTTPException(status_code=503, detail='Narration is not configured')
    if voice not in TTS_VOICES:
        raise HTTPException(status_code=400, detail='Unknown voice')
    # NARRATION ACCESS POLICY: sign-in required; premium hears it all; free members hear the
    # full track on free-audio essays (newsletter/shipping) or after a per-essay unlock,
    # otherwise a 20s preview
    if not user:
        raise HTTPException(status_code=401, detail='Sign in to listen to narrations, free accounts get a 20-second preview.')
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    blocks = post.get('content_blocks', [])
    entitled = await is_entitled(user)
    # PREMIUM PILLARS: narration is exclusive to Premium members (no clip, no unlock)
    if premium_audio_only(post) and not entitled:
        raise HTTPException(status_code=403, detail='Narrations for this essay are exclusive to Premium members.')
    full_access = entitled or has_free_audio(post) or owns_audio(user, slug)
    from services.tts_service import get_or_generate_audio
    try:
        audio, from_cache = await get_or_generate_audio(post, voice, blocks, 'full')
    except Exception as e:
        logger.error(f'TTS generation failed for {slug}: {e}')
        if 'quota_exceeded' in str(e):
            raise HTTPException(status_code=503,
                                detail='Narration for this essay is temporarily unavailable while audio credits are being refilled. Please check back soon.')
        raise HTTPException(status_code=502, detail='Narration is temporarily unavailable. Try again shortly.')
    scope = 'full'
    if not full_access:
        # 20-second preview clip for free members, sliced from the cached MP3
        # (64 kbps ≈ 8 KB/s -> 20s ≈ 160 KB); no extra ElevenLabs credits are spent.
        scope = 'clip'
        audio = audio[:AUDIO_CLIP_BYTES]
    return Response(content=audio, media_type='audio/mpeg', headers={
        'Cache-Control': 'private, max-age=86400',
        'X-Audio-Cache': 'hit' if from_cache else 'generated',
        'X-Audio-Scope': scope,
    })


@router.get('/founding-members')
async def founding_members():
    """Public thank-you wall: readers who backed the publication as Founding Members."""
    subs = await db.subscriptions.find({'plan': {'$in': ['founding', 'founding_monthly']},
                                        'status': 'active'}).sort('created_at', 1).to_list(500)
    members, seen = [], set()
    for s in subs:
        uid = s.get('user_id')
        if not uid or uid in seen:
            continue
        seen.add(uid)
        u = await db.users.find_one({'id': uid})
        if u:
            members.append({'name': u.get('name') or u['email'].split('@')[0].title(),
                            'since': (s.get('created_at') or '')[:10]})
    return {'members': members, 'count': len(members)}


@router.post('/posts/{slug}/audio/listen')
async def track_audio_listen(slug: str, user=Depends(get_optional_user)):
    """Count a narration play: bump the post's listens counter + log an analytics event."""
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    await db.posts.update_one({'slug': slug}, {'$inc': {'listens': 1}})
    await db.analytics.insert_one({
        'id': str(uuid.uuid4()), 'event': 'narration_listen', 'path': f'/post/{slug}',
        'meta': {'slug': slug, 'title': post['title']},
        'user_id': user['id'] if user else None,
        'created_at': iso(now_utc()),
    })
    return {'ok': True}


@router.post('/posts/{slug}/audio/progress')
async def track_audio_progress(slug: str, body: AudioProgressIn, user=Depends(get_optional_user)):
    """Record how far a listener got: milestone counters power the admin completion rate."""
    if body.milestone not in (25, 50, 75, 100):
        raise HTTPException(status_code=400, detail='Milestone must be 25, 50, 75 or 100')
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    await db.posts.update_one({'slug': slug}, {'$inc': {f'listen_milestones.{body.milestone}': 1}})
    return {'ok': True}


@router.get('/audio/voices')
async def audio_voices():
    return {'enabled': TTS_ENABLED,
            'voices': [{'key': k, 'label': v['label']} for k, v in TTS_VOICES.items()]}


@router.get('/audio/library')
async def audio_library(user=Depends(get_current_user)):
    """My Audio Library: narrations this reader bought a la carte, replayable anytime."""
    slugs = user.get('purchased_audio_slugs') or []
    if not slugs:
        return {'items': []}
    posts = await db.posts.find({'slug': {'$in': slugs}, **published_query()}).to_list(200)
    by_slug = {p['slug']: p for p in posts}
    # newest purchase first ($addToSet appends, so reverse the stored order)
    items = [post_summary(by_slug[s]) for s in reversed(slugs) if s in by_slug]
    return {'items': items}


# ---------------------- SEO ----------------------

@router.get('/sitemap.xml')
async def sitemap():
    posts = await db.posts.find(published_query()).to_list(1000)
    today = iso(now_utc())[:10]
    entries = [(FRONTEND_URL, today), (f'{FRONTEND_URL}/archive', today),
               (f'{FRONTEND_URL}/pricing', None), (f'{FRONTEND_URL}/about', None),
               (f'{FRONTEND_URL}/glossary', today),
               (f'{FRONTEND_URL}/books', None),
               (f'{FRONTEND_URL}/briefings', today)]
    entries += [(f'{FRONTEND_URL}/topics/{slug}', today) for slug in CATEGORIES]
    entries += [(f'{FRONTEND_URL}/category/{slug}', None) for slug in CATEGORIES]
    entries += [(f"{FRONTEND_URL}/post/{p['slug']}",
                 (p.get('updated_at') or p.get('published_at') or '')[:10] or None) for p in posts]
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, lastmod in entries:
        body += f'  <url><loc>{u}</loc>' + (f'<lastmod>{lastmod}</lastmod>' if lastmod else '') + '</url>\n'
    body += '</urlset>'
    return Response(content=body, media_type='application/xml')


def _xml_escape(s: str) -> str:
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


@router.get('/feed.xml')
async def rss_feed():
    """RSS 2.0: full text for open (free) essays, preview + link for locked ones."""
    posts = await db.posts.find(published_query()).sort('published_at', -1).to_list(50)
    items = []
    from email.utils import format_datetime
    from datetime import datetime
    for p in posts:
        clean(p)
        link = f"{FRONTEND_URL}/post/{p['slug']}"
        try:
            pub = format_datetime(datetime.fromisoformat(p.get('published_at', '')))
        except (ValueError, TypeError):
            pub = ''
        locked = p.get('tier') == 'premium' or 'lounge' in (p.get('tags') or [])
        blocks = p.get('content_blocks', [])
        body_blocks = preview_slice(blocks) if locked else blocks
        content = ''.join(f'<p>{_xml_escape(b)}</p>' for b in body_blocks if not b.startswith('## '))
        if locked:
            content += (f'<p><em>This is a premium essay preview. '
                        f'<a href="{link}">Read the full essay on The Trading Narrative</a>.</em></p>')
        items.append(
            f'<item><title>{_xml_escape(p["title"])}</title>'
            f'<link>{link}</link><guid isPermaLink="true">{link}</guid>'
            f'<pubDate>{pub}</pubDate>'
            f'<description>{_xml_escape(p.get("excerpt", ""))}</description>'
            f'<content:encoded><![CDATA[{content}]]></content:encoded>'
            f'</item>')
    body = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
            f'<channel><title>The Trading Narrative</title><link>{FRONTEND_URL}</link>'
            f'<description>Sharp narratives on markets, trading technology, and the systems behind the desk.</description>'
            + ''.join(items) + '</channel></rss>')
    return Response(content=body, media_type='application/rss+xml')


@router.get('/health')
async def health():
    return {'status': 'ok', 'app': 'The Trading Narrative'}
