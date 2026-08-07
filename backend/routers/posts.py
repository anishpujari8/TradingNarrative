"""Public content routes: categories, posts, comments, notifications, bookmarks,
recommendations, briefings, sitemap, health."""
import re
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response

from config import CATEGORIES, PREVIEW_BLOCKS, FRONTEND_URL
from db import db
from utils import now_utc, iso, clean, post_summary, published_query
from security import get_optional_user, get_current_user, is_entitled
from schemas import CommentIn, BookmarkToggleIn

router = APIRouter(prefix='/api')


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


# ---------------------- SEO ----------------------

@router.get('/sitemap.xml')
async def sitemap():
    posts = await db.posts.find(published_query()).to_list(1000)
    urls = [FRONTEND_URL, f'{FRONTEND_URL}/archive', f'{FRONTEND_URL}/pricing', f'{FRONTEND_URL}/about']
    urls += [f'{FRONTEND_URL}/category/{slug}' for slug in CATEGORIES]
    urls += [f"{FRONTEND_URL}/post/{p['slug']}" for p in posts]
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    body += ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls)
    body += '</urlset>'
    return Response(content=body, media_type='application/xml')


@router.get('/health')
async def health():
    return {'status': 'ok', 'app': 'The Trading Narrative'}
