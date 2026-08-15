"""Community Lounge routes (premium members only): announcements, threads, replies, profiles."""
import uuid
from datetime import datetime, timezone, timedelta
from html import escape as _esc

from fastapi import APIRouter, HTTPException, Depends

from config import FRONTEND_URL, logger
from db import db
from utils import now_utc, iso, clean
from security import get_admin_user, get_premium_user, is_entitled
from schemas import AnnouncementIn, CommunityThreadIn, CommunityReplyIn, NarrativeTakeIn, NarrativeReactIn
from services.emailer import log_email

router = APIRouter(prefix='/api')

NARRATIVE_TAGS = {'bullish', 'bearish', 'insight'}
NARRATIVE_REACTIONS = ('📈', '📉', '💡')

# The Lounge identity: Signal Wolf mascot + plum accent, kept in sync with lib/pillars.js
LOUNGE_ACCENT = '#a04f86'


def _lounge_reply_html(actor: str, title: str, preview: str, thread_url: str) -> str:
    """Signal Wolf branded email for Lounge reply notifications."""
    wolf_url = f'{FRONTEND_URL}/pillars/lounge.webp'
    actor, title, preview = _esc(actor), _esc(title), _esc(preview)
    return f'''
<div style="max-width:560px;margin:0 auto;font-family:Georgia,serif;background:#faf7f9;border:1px solid #e7d3e0;border-radius:12px;overflow:hidden">
  <div style="background:#161a2e;padding:26px 24px;text-align:center">
    <img src="{wolf_url}" alt="The Signal Wolf" width="84" height="84" style="border-radius:50%;border:3px solid {LOUNGE_ACCENT}">
    <p style="color:{LOUNGE_ACCENT};font-family:monospace;font-size:11px;letter-spacing:3px;text-transform:uppercase;margin:14px 0 4px">The Lounge</p>
    <p style="color:#f2ede7;font-size:18px;margin:0;font-weight:600">The pack has news for you</p>
  </div>
  <div style="padding:26px 28px">
    <p style="font-size:15px;color:#2b2b2b;line-height:1.6;margin:0 0 14px"><strong>{actor}</strong> replied to your discussion:</p>
    <p style="font-size:17px;font-weight:600;color:#161a2e;margin:0 0 14px">&ldquo;{title}&rdquo;</p>
    <blockquote style="margin:0 0 22px;padding:12px 16px;border-left:3px solid {LOUNGE_ACCENT};background:#f4e9f0;color:#4a3a44;font-size:14px;line-height:1.6">{preview}</blockquote>
    <a href="{thread_url}" style="display:inline-block;background:{LOUNGE_ACCENT};color:#ffffff;text-decoration:none;font-family:sans-serif;font-size:14px;font-weight:600;padding:12px 22px;border-radius:8px">Open in the Lounge</a>
  </div>
  <div style="padding:14px 28px;border-top:1px solid #e7d3e0">
    <p style="font-size:12px;color:#8a7a84;font-family:sans-serif;margin:0">The Signal Wolf howls only when it matters &mdash; you are getting this because a fellow member replied to you.</p>
  </div>
</div>'''


def community_author(user):
    return {'id': user['id'], 'name': user.get('name') or user['email'].split('@')[0],
            'role': user.get('role', 'user')}


# ---------------------- Market Narrative (editor's live takes) ----------------------

def _narrative_out(t, user_id: str):
    """Shape a take for the API: aggregate reactions + the caller's own reaction."""
    reactions = t.get('reactions', {})  # {user_id: emoji}
    counts = {e: 0 for e in NARRATIVE_REACTIONS}
    for e in reactions.values():
        if e in counts:
            counts[e] += 1
    return {'id': t['id'], 'body': t['body'], 'tag': t.get('tag'),
            'author': t['author'], 'created_at': t['created_at'],
            'reactions': counts, 'my_reaction': reactions.get(user_id)}


@router.get('/community/narrative')
async def narrative_feed(user=Depends(get_premium_user)):
    takes = await db.narrative_takes.find().sort('created_at', -1).to_list(100)
    return {'takes': [_narrative_out(clean(t), user['id']) for t in takes]}


@router.post('/community/narrative')
async def narrative_create(body: NarrativeTakeIn, admin=Depends(get_admin_user)):
    text = body.body.strip()
    if len(text) < 3:
        raise HTTPException(status_code=400, detail='Write a little more than that.')
    tag = body.tag if body.tag in NARRATIVE_TAGS else None
    take = {'id': str(uuid.uuid4()), 'body': text[:2000], 'tag': tag,
            'author': community_author(admin), 'reactions': {},
            'created_at': iso(now_utc())}
    await db.narrative_takes.insert_one(dict(take))
    return _narrative_out(take, admin['id'])


@router.delete('/community/narrative/{nid}')
async def narrative_delete(nid: str, admin=Depends(get_admin_user)):
    res = await db.narrative_takes.delete_one({'id': nid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Take not found')
    return {'ok': True}


@router.post('/community/narrative/{nid}/react')
async def narrative_react(nid: str, body: NarrativeReactIn, user=Depends(get_premium_user)):
    if body.emoji not in NARRATIVE_REACTIONS:
        raise HTTPException(status_code=400, detail='Unknown reaction')
    take = await db.narrative_takes.find_one({'id': nid})
    if not take:
        raise HTTPException(status_code=404, detail='Take not found')
    reactions = take.get('reactions', {})
    # toggle: same emoji removes it, different emoji switches (one reaction per member)
    if reactions.get(user['id']) == body.emoji:
        reactions.pop(user['id'], None)
    else:
        reactions[user['id']] = body.emoji
    await db.narrative_takes.update_one({'id': nid}, {'$set': {'reactions': reactions}})
    take['reactions'] = reactions
    return _narrative_out(clean(take), user['id'])


# ---------------------- Early access (scheduled drafts for members) ----------------------

@router.get('/community/early-access')
async def early_access_list(user=Depends(get_premium_user)):
    now = iso(now_utc())
    drafts = await db.posts.find({'status': 'scheduled', 'publish_at': {'$gt': now}}) \
        .sort('publish_at', 1).to_list(20)
    return {'drafts': [{
        'id': d['id'], 'slug': d['slug'], 'title': d['title'], 'excerpt': d.get('excerpt', ''),
        'category': d.get('category'), 'tier': d.get('tier'), 'edition': d.get('edition'),
        'cover_image': d.get('cover_image'), 'publish_at': d.get('publish_at'),
    } for d in map(clean, drafts)]}


@router.get('/community/announcements')
async def community_announcements(user=Depends(get_premium_user)):
    items = await db.community_announcements.find({}).sort('created_at', -1).to_list(50)
    now = iso(now_utc())
    out = []
    for a in items:
        clean(a)
        scheduled = bool(a.get('publish_at') and a['publish_at'] > now)
        if scheduled and user.get('role') != 'admin':
            continue  # members only see published announcements
        a['scheduled'] = scheduled
        out.append(a)
    return {'announcements': out}


@router.post('/community/announcements')
async def community_create_announcement(body: AnnouncementIn, admin=Depends(get_admin_user)):
    title, text = body.title.strip(), body.body.strip()
    if not (3 <= len(title) <= 200):
        raise HTTPException(status_code=400, detail='Title must be 3-200 characters')
    if not (1 <= len(text) <= 5000):
        raise HTTPException(status_code=400, detail='Body must be 1-5000 characters')
    publish_at = None
    if body.publish_at:
        try:
            dt = datetime.fromisoformat(body.publish_at.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            publish_at = iso(dt)
        except Exception:
            raise HTTPException(status_code=400, detail='Invalid publish_at datetime')
    item = {'id': str(uuid.uuid4()), 'title': title, 'body': text,
            'author': community_author(admin), 'publish_at': publish_at,
            'created_at': iso(now_utc())}
    await db.community_announcements.insert_one(dict(item))
    item = clean(item)
    item['scheduled'] = bool(publish_at and publish_at > iso(now_utc()))
    return item


@router.put('/community/announcements/{aid}')
async def community_edit_announcement(aid: str, body: AnnouncementIn, admin=Depends(get_admin_user)):
    existing = await db.community_announcements.find_one({'id': aid})
    if not existing:
        raise HTTPException(status_code=404, detail='Announcement not found')
    title, text = body.title.strip(), body.body.strip()
    if not (3 <= len(title) <= 200):
        raise HTTPException(status_code=400, detail='Title must be 3-200 characters')
    if not (1 <= len(text) <= 5000):
        raise HTTPException(status_code=400, detail='Body must be 1-5000 characters')
    publish_at = None
    if body.publish_at:
        try:
            dt = datetime.fromisoformat(body.publish_at.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            publish_at = iso(dt)
        except Exception:
            raise HTTPException(status_code=400, detail='Invalid publish_at datetime')
    await db.community_announcements.update_one({'id': aid}, {'$set': {
        'title': title, 'body': text, 'publish_at': publish_at,
        'edited_at': iso(now_utc())}})
    item = await db.community_announcements.find_one({'id': aid})
    item = clean(item)
    item['scheduled'] = bool(publish_at and publish_at > iso(now_utc()))
    return item


@router.delete('/community/announcements/{aid}')
async def community_delete_announcement(aid: str, admin=Depends(get_admin_user)):
    result = await db.community_announcements.delete_one({'id': aid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Announcement not found')
    return {'ok': True}


@router.get('/community/members/{uid}')
async def community_member_profile(uid: str, user=Depends(get_premium_user)):
    member = await db.users.find_one({'id': uid})
    if not member:
        raise HTTPException(status_code=404, detail='Member not found')
    premium = await is_entitled(member)
    thread_count = await db.community_threads.count_documents({'author.id': uid})
    reply_count = await db.community_replies.count_documents({'author.id': uid})
    recent = await db.community_threads.find({'author.id': uid}).sort('created_at', -1).limit(5).to_list(5)
    return {
        'id': member['id'],
        'name': member.get('name') or member['email'].split('@')[0],
        'role': member.get('role', 'user'),
        'is_premium': premium,
        'joined': member.get('created_at'),
        'thread_count': thread_count,
        'reply_count': reply_count,
        'recent_threads': [{'id': t['id'], 'title': t['title'], 'created_at': t['created_at'],
                            'reply_count': t.get('reply_count', 0)} for t in recent],
    }


@router.get('/community/threads')
async def community_threads(user=Depends(get_premium_user)):
    threads = await db.community_threads.find({}).sort(
        [('pinned', -1), ('last_activity_at', -1)]).to_list(100)
    return {'threads': [clean(t) for t in threads]}


@router.post('/community/threads')
async def community_create_thread(body: CommunityThreadIn, user=Depends(get_premium_user)):
    title, text = body.title.strip(), body.body.strip()
    if not (3 <= len(title) <= 200):
        raise HTTPException(status_code=400, detail='Title must be 3-200 characters')
    if not (1 <= len(text) <= 5000):
        raise HTTPException(status_code=400, detail='Body must be 1-5000 characters')
    # basic rate limit: max 5 threads per hour per member
    hour_ago = iso(now_utc() - timedelta(hours=1))
    recent = await db.community_threads.count_documents({'author.id': user['id'], 'created_at': {'$gte': hour_ago}})
    if recent >= 5:
        raise HTTPException(status_code=429, detail='Slow down — you can start up to 5 discussions per hour.')
    thread = {'id': str(uuid.uuid4()), 'title': title, 'body': text,
              'author': community_author(user), 'reply_count': 0, 'pinned': False, 'locked': False,
              'created_at': iso(now_utc()), 'last_activity_at': iso(now_utc())}
    await db.community_threads.insert_one(dict(thread))
    return clean(thread)


@router.get('/community/threads/{tid}')
async def community_thread_detail(tid: str, user=Depends(get_premium_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    replies = await db.community_replies.find({'thread_id': tid}).sort('created_at', 1).to_list(500)
    return {'thread': clean(thread), 'replies': [clean(r) for r in replies]}


@router.post('/community/threads/{tid}/replies')
async def community_reply(tid: str, body: CommunityReplyIn, user=Depends(get_premium_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    if thread.get('locked'):
        raise HTTPException(status_code=403, detail='This discussion is locked — it stays readable but no new replies.')
    text = body.body.strip()
    if not (1 <= len(text) <= 5000):
        raise HTTPException(status_code=400, detail='Reply must be 1-5000 characters')
    hour_ago = iso(now_utc() - timedelta(hours=1))
    recent = await db.community_replies.count_documents({'author.id': user['id'], 'created_at': {'$gte': hour_ago}})
    if recent >= 30:
        raise HTTPException(status_code=429, detail='Slow down — up to 30 replies per hour.')
    reply = {'id': str(uuid.uuid4()), 'thread_id': tid, 'body': text,
             'author': community_author(user), 'created_at': iso(now_utc())}
    await db.community_replies.insert_one(dict(reply))
    await db.community_threads.update_one({'id': tid}, {
        '$inc': {'reply_count': 1}, '$set': {'last_activity_at': iso(now_utc())}})
    # bell notification for the discussion author
    if thread['author']['id'] != user['id']:
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()), 'user_id': thread['author']['id'], 'type': 'lounge_reply',
            'actor_name': reply['author']['name'], 'thread_id': tid, 'thread_title': thread['title'],
            'preview': text[:140], 'read': False, 'created_at': iso(now_utc()),
        })
        # Signal Wolf email so the pack identity carries into the inbox (never blocks the reply)
        try:
            author_doc = await db.users.find_one({'id': thread['author']['id']})
            if author_doc and author_doc.get('email'):
                thread_url = f'{FRONTEND_URL}/lounge?thread={tid}'
                actor = reply['author']['name']
                await log_email(
                    author_doc['email'],
                    f'{actor} replied in the Lounge: {thread["title"][:60]}',
                    (f'{actor} replied to your discussion "{thread["title"]}":\n\n'
                     f'{text[:300]}\n\nOpen it in the Lounge: {thread_url}'),
                    'lounge_reply',
                    html=_lounge_reply_html(actor, thread['title'], text[:300], thread_url),
                )
        except Exception as e:
            logger.warning(f'Lounge reply email failed (non-blocking): {str(e)[:150]}')
    return clean(reply)


@router.post('/community/threads/{tid}/pin')
async def community_pin_thread(tid: str, admin=Depends(get_admin_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    new_state = not thread.get('pinned', False)
    await db.community_threads.update_one({'id': tid}, {'$set': {'pinned': new_state}})
    return {'ok': True, 'pinned': new_state}


@router.post('/community/threads/{tid}/lock')
async def community_lock_thread(tid: str, admin=Depends(get_admin_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    new_state = not thread.get('locked', False)
    await db.community_threads.update_one({'id': tid}, {'$set': {'locked': new_state}})
    return {'ok': True, 'locked': new_state}


@router.delete('/community/threads/{tid}')
async def community_delete_thread(tid: str, user=Depends(get_premium_user)):
    thread = await db.community_threads.find_one({'id': tid})
    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    if user.get('role') != 'admin' and thread['author']['id'] != user['id']:
        raise HTTPException(status_code=403, detail='You can only delete your own threads')
    await db.community_threads.delete_one({'id': tid})
    await db.community_replies.delete_many({'thread_id': tid})
    return {'ok': True}


@router.delete('/community/replies/{rid}')
async def community_delete_reply(rid: str, user=Depends(get_premium_user)):
    reply = await db.community_replies.find_one({'id': rid})
    if not reply:
        raise HTTPException(status_code=404, detail='Reply not found')
    if user.get('role') != 'admin' and reply['author']['id'] != user['id']:
        raise HTTPException(status_code=403, detail='You can only delete your own replies')
    await db.community_replies.delete_one({'id': rid})
    await db.community_threads.update_one({'id': reply['thread_id']}, {'$inc': {'reply_count': -1}})
    return {'ok': True}
