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
