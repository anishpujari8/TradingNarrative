"""Content Sync: one-click copy of published preview articles to the production site."""
import asyncio

import requests
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from config import PRODUCTION_SITE_URL, logger
from db import db
from utils import published_query
from security import get_admin_user

router = APIRouter(prefix='/api')


class SyncPushIn(BaseModel):
    password: str = Field(min_length=1)


def _prod_get_posts():
    r = requests.get(f'{PRODUCTION_SITE_URL}/api/posts?limit=100', timeout=20)
    r.raise_for_status()
    return r.json()['posts']


SYNC_FIELDS = ['title', 'excerpt', 'category', 'tier', 'cover_image', 'content_blocks',
               'tags', 'featured', 'edition']
# public post listings omit/truncate content (paywall), so pre-auth diffs skip content_blocks
DIFF_PUBLIC_FIELDS = [f for f in SYNC_FIELDS if f != 'content_blocks']


def _field_diffs(local, remote, fields=None):
    """Which syncable fields differ between the preview post and its production copy."""
    changed = []
    for f in (fields or SYNC_FIELDS):
        lv = local.get(f) if f != 'tags' else (local.get('tags') or [])
        rv = remote.get(f) if f != 'tags' else (remote.get('tags') or [])
        if f == 'featured':
            lv, rv = bool(lv), bool(rv)
        if lv != rv:
            changed.append(f)
    return changed


async def _compute_missing():
    """Published preview posts whose slug does not exist on production."""
    try:
        prod_posts = await asyncio.to_thread(_prod_get_posts)
    except Exception as e:
        logger.warning(f'Sync: production unreachable: {e}')
        raise HTTPException(status_code=502, detail='Could not reach the production site. Try again in a minute.')
    prod_slugs = {p['slug'] for p in prod_posts}
    preview_posts = await db.posts.find(published_query()).sort('published_at', 1).to_list(200)
    missing = [p for p in preview_posts if p['slug'] not in prod_slugs]
    return missing, len(prod_posts), preview_posts, prod_posts


@router.get('/admin/sync/diff')
async def sync_diff(admin=Depends(get_admin_user)):
    missing, prod_total, preview_posts, prod_posts = await _compute_missing()
    # posts on both sides whose public-facing fields drifted (e.g. tier flipped to premium here)
    prod_by_slug = {p['slug']: p for p in prod_posts}
    outdated = []
    for p in preview_posts:
        remote = prod_by_slug.get(p['slug'])
        if not remote:
            continue
        changed = _field_diffs(p, remote, DIFF_PUBLIC_FIELDS)
        if changed:
            outdated.append({'slug': p['slug'], 'title': p['title'], 'changed': changed,
                             'tier': p.get('tier', 'free')})
    return {
        'production_url': PRODUCTION_SITE_URL,
        'production_published': prod_total,
        'missing': [{'slug': p['slug'], 'title': p['title'], 'category': p['category'],
                     'tier': p.get('tier', 'free'), 'edition': p.get('edition')} for p in missing],
        'outdated': outdated,
    }


@router.post('/admin/sync/push')
async def sync_push(body: SyncPushIn, admin=Depends(get_admin_user)):
    missing, _, preview_posts, _ = await _compute_missing()

    def _login():
        r = requests.post(f'{PRODUCTION_SITE_URL}/api/auth/login',
                          json={'email': admin['email'], 'password': body.password}, timeout=20)
        return r

    resp = await asyncio.to_thread(_login)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail='Production sign-in failed — check the production admin password.')
    # cookie-auth era: the session JWT arrives as the httpOnly cookie; older builds returned it in the body
    token = resp.json().get('token') or resp.cookies.get('ttn_session')
    if not token:
        raise HTTPException(status_code=502, detail='Production sign-in succeeded but returned no session.')
    headers = {'Authorization': f'Bearer {token}'}

    def _payload(p):
        return {
            'title': p['title'], 'excerpt': p.get('excerpt', ''), 'category': p['category'],
            'tier': p.get('tier', 'free'), 'cover_image': p.get('cover_image', ''),
            'content_blocks': p.get('content_blocks', []), 'tags': p.get('tags', []),
            'featured': p.get('featured', False), 'status': 'published',
            'edition': p.get('edition'),
        }

    results = []
    pushed = 0
    for p in missing:
        def _push(pl=_payload(p)):
            return requests.post(f'{PRODUCTION_SITE_URL}/api/admin/posts', json=pl, headers=headers, timeout=30)

        try:
            r = await asyncio.to_thread(_push)
            ok = r.status_code == 200
            if ok:
                pushed += 1
            results.append({'title': p['title'], 'slug': p['slug'], 'ok': ok, 'action': 'created',
                            'detail': None if ok else r.text[:150]})
        except Exception as e:
            results.append({'title': p['title'], 'slug': p['slug'], 'ok': False, 'action': 'created',
                            'detail': str(e)[:150]})

    # UPDATE MODE: bring already-live posts in line with preview (tier changes, edits, etc.)
    updated = 0
    def _prod_admin_posts():
        return requests.get(f'{PRODUCTION_SITE_URL}/api/admin/posts', headers=headers, timeout=30)

    try:
        r = await asyncio.to_thread(_prod_admin_posts)
        r.raise_for_status()
        prod_admin = {p['slug']: p for p in r.json()['posts']}
    except Exception as e:
        logger.warning(f'Sync: could not list production posts for update pass: {e}')
        prod_admin = {}
    for p in preview_posts:
        remote = prod_admin.get(p['slug'])
        if not remote or remote.get('status') != 'published':
            continue
        changed = _field_diffs(p, remote)
        if not changed:
            continue

        def _put(pid=remote['id'], pl=_payload(p)):
            return requests.put(f'{PRODUCTION_SITE_URL}/api/admin/posts/{pid}', json=pl,
                                headers=headers, timeout=30)

        try:
            r = await asyncio.to_thread(_put)
            ok = r.status_code == 200
            if ok:
                updated += 1
            results.append({'title': p['title'], 'slug': p['slug'], 'ok': ok, 'action': 'updated',
                            'detail': ', '.join(changed) if ok else r.text[:150]})
        except Exception as e:
            results.append({'title': p['title'], 'slug': p['slug'], 'ok': False, 'action': 'updated',
                            'detail': str(e)[:150]})
    logger.info(f'Sync to production: created {pushed}/{len(missing)}, updated {updated} articles')
    return {'ok': True, 'pushed': pushed, 'updated': updated, 'total': len(missing), 'results': results,
            'message': None if (missing or updated) else 'Production already matches preview.'}


# ---------------------- narration sync (preview cache -> production cache) ----------------------

@router.post('/admin/sync/narrations')
async def sync_narrations(body: SyncPushIn, admin=Depends(get_admin_user)):
    """Push locally cached narrations to production so the live site serves them instantly —
    without spending any new ElevenLabs credits. Skips narrations production already has."""
    import base64

    def _login():
        return requests.post(f'{PRODUCTION_SITE_URL}/api/auth/login',
                             json={'email': admin['email'], 'password': body.password}, timeout=20)

    resp = await asyncio.to_thread(_login)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail='Production sign-in failed — check the production admin password.')
    token = resp.json().get('token') or resp.cookies.get('ttn_session')
    if not token:
        raise HTTPException(status_code=502, detail='Production sign-in succeeded but returned no session.')
    headers = {'Authorization': f'Bearer {token}'}

    # what does production already have cached, and which posts exist there?
    def _prod_narrations():
        return requests.get(f'{PRODUCTION_SITE_URL}/api/admin/narrations', headers=headers, timeout=20)

    prod_cached_full = set()
    prod_slugs = None
    try:
        r = await asyncio.to_thread(_prod_narrations)
        if r.status_code == 200:
            data = r.json()
            prod_slugs = {e['slug'] for e in data.get('essays', [])}
            prod_cached_full = {(e['slug'], s) for e in data.get('essays', []) for s in e.get('scopes', [])}
    except Exception as e:
        logger.warning(f'Narration sync: could not read production narration status: {e}')
    if prod_slugs is None:
        try:
            prod_slugs = {p['slug'] for p in await asyncio.to_thread(_prod_get_posts)}
        except Exception:
            raise HTTPException(status_code=502, detail='Could not reach the production site. Try again in a minute.')

    local = await db.audio_cache.find({}).to_list(200)
    results, pushed, skipped = [], 0, 0
    for doc in local:
        slug, voice, scope = doc['post_slug'], doc.get('voice', 'male'), doc.get('scope', 'full')
        label = f'{slug} ({voice}/{scope})'
        audio_bytes = bytes(doc.get('audio') or b'')
        if len(audio_bytes) < 50 * 1024:
            continue  # never ship corrupt/truncated audio to the live site
        if slug not in prod_slugs:
            continue  # essay not on production — nothing to attach the audio to
        if (slug, scope) in prod_cached_full:
            skipped += 1
            results.append({'label': label, 'ok': True, 'skipped': True, 'detail': 'Already on production'})
            continue
        payload = {'post_slug': slug, 'voice': voice, 'scope': scope,
                   'audio_b64': base64.b64encode(audio_bytes).decode(),
                   'chars': doc.get('chars', 0)}

        def _push(pl=payload):
            return requests.post(f'{PRODUCTION_SITE_URL}/api/admin/audio-cache/import',
                                 json=pl, headers=headers, timeout=120)

        try:
            r = await asyncio.to_thread(_push)
            if r.status_code == 200:
                pushed += 1
                results.append({'label': label, 'ok': True, 'detail': None})
            elif r.status_code == 404 and 'not published' not in r.text:
                results.append({'label': label, 'ok': False,
                                'detail': 'Production does not have the import endpoint yet — redeploy first.'})
            else:
                results.append({'label': label, 'ok': False, 'detail': r.text[:150]})
        except Exception as e:
            results.append({'label': label, 'ok': False, 'detail': str(e)[:150]})
    logger.info(f'Narration sync: pushed {pushed}, skipped {skipped} (already live)')
    return {'ok': True, 'pushed': pushed, 'skipped': skipped, 'results': results}
