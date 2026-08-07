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
    return missing, len(prod_posts)


@router.get('/admin/sync/diff')
async def sync_diff(admin=Depends(get_admin_user)):
    missing, prod_total = await _compute_missing()
    return {
        'production_url': PRODUCTION_SITE_URL,
        'production_published': prod_total,
        'missing': [{'slug': p['slug'], 'title': p['title'], 'category': p['category'],
                     'tier': p.get('tier', 'free'), 'edition': p.get('edition')} for p in missing],
    }


@router.post('/admin/sync/push')
async def sync_push(body: SyncPushIn, admin=Depends(get_admin_user)):
    missing, _ = await _compute_missing()
    if not missing:
        return {'ok': True, 'pushed': 0, 'results': [], 'message': 'Production already has every published article.'}

    def _login():
        r = requests.post(f'{PRODUCTION_SITE_URL}/api/auth/login',
                          json={'email': admin['email'], 'password': body.password}, timeout=20)
        return r

    resp = await asyncio.to_thread(_login)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail='Production sign-in failed — check the production admin password.')
    token = resp.json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    results = []
    pushed = 0
    for p in missing:
        payload = {
            'title': p['title'], 'excerpt': p.get('excerpt', ''), 'category': p['category'],
            'tier': p.get('tier', 'free'), 'cover_image': p.get('cover_image', ''),
            'content_blocks': p.get('content_blocks', []), 'tags': p.get('tags', []),
            'featured': p.get('featured', False), 'status': 'published',
            'edition': p.get('edition'),
        }

        def _push(pl=payload):
            return requests.post(f'{PRODUCTION_SITE_URL}/api/admin/posts', json=pl, headers=headers, timeout=30)

        try:
            r = await asyncio.to_thread(_push)
            ok = r.status_code == 200
            if ok:
                pushed += 1
            results.append({'title': p['title'], 'slug': p['slug'], 'ok': ok,
                            'detail': None if ok else r.text[:150]})
        except Exception as e:
            results.append({'title': p['title'], 'slug': p['slug'], 'ok': False, 'detail': str(e)[:150]})
    logger.info(f'Sync to production: pushed {pushed}/{len(missing)} articles')
    return {'ok': True, 'pushed': pushed, 'total': len(missing), 'results': results}


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
    headers = {'Authorization': f"Bearer {resp.json()['token']}"}

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
