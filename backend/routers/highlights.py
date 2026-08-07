"""Reader highlights: save favourite lines from essays to a personal highlights page."""
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from config import CATEGORIES, PREVIEW_BLOCKS
from db import db
from utils import now_utc, iso, clean, published_query
from security import get_current_user, is_entitled
from schemas import HighlightIn

router = APIRouter(prefix='/api')

MAX_HIGHLIGHTS_PER_USER = 500
MAX_HIGHLIGHTS_PER_POST = 50


@router.post('/highlights')
async def create_highlight(body: HighlightIn, user=Depends(get_current_user)):
    post = await db.posts.find_one({'slug': body.slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    blocks = post.get('content_blocks', [])
    # respect the server-side paywall: non-premium readers can only highlight the preview
    if post.get('tier') == 'premium' and not await is_entitled(user):
        blocks = blocks[:PREVIEW_BLOCKS]
    if body.block_index >= len(blocks):
        raise HTTPException(status_code=400, detail='Invalid paragraph reference')
    text = ' '.join(body.text.split())  # normalise whitespace
    block_norm = ' '.join(blocks[body.block_index].split())
    if text not in block_norm:
        raise HTTPException(status_code=400, detail='Selected text no longer matches this essay')
    existing = await db.highlights.find_one({'user_id': user['id'], 'post_id': post['id'], 'text': text})
    if existing:
        return {**clean(existing), 'already': True}
    total = await db.highlights.count_documents({'user_id': user['id']})
    if total >= MAX_HIGHLIGHTS_PER_USER:
        raise HTTPException(status_code=429, detail='Highlight limit reached — remove some older highlights first.')
    per_post = await db.highlights.count_documents({'user_id': user['id'], 'post_id': post['id']})
    if per_post >= MAX_HIGHLIGHTS_PER_POST:
        raise HTTPException(status_code=429, detail='You have reached the highlight limit for this essay.')
    item = {
        'id': str(uuid.uuid4()), 'user_id': user['id'],
        'post_id': post['id'], 'post_slug': post['slug'], 'post_title': post['title'],
        'category': post['category'],
        'category_label': CATEGORIES.get(post['category'], post['category']),
        'block_index': body.block_index, 'text': text,
        'created_at': iso(now_utc()),
    }
    await db.highlights.insert_one(dict(item))
    return {**clean(item), 'already': False}


@router.get('/highlights')
async def list_highlights(user=Depends(get_current_user), slug: Optional[str] = Query(None)):
    query = {'user_id': user['id']}
    if slug:
        query['post_slug'] = slug
    items = await db.highlights.find(query).sort('created_at', -1).to_list(MAX_HIGHLIGHTS_PER_USER)
    return {'highlights': [clean(h) for h in items], 'total': len(items)}


@router.delete('/highlights/{hid}')
async def delete_highlight(hid: str, user=Depends(get_current_user)):
    h = await db.highlights.find_one({'id': hid})
    if not h:
        raise HTTPException(status_code=404, detail='Highlight not found')
    if h['user_id'] != user['id'] and user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='You can only remove your own highlights')
    await db.highlights.delete_one({'id': hid})
    return {'ok': True}
