"""Admin routes: post CRUD, subscribers, issues, stats, email status/test/logs."""
import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends, Query

from config import (CATEGORIES, FRONTEND_URL, EMAIL_ENABLED, EMAIL_FROM_NAME,
                    EMAIL_REPLY_TO, GMAIL_SMTP_USER)
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
    return {
        'pageviews': pageviews, 'pageviews_7d': pageviews_7d,
        'newsletter_subscribers': nl_subs, 'users': users,
        'premium_subscribers': premium, 'checkouts': checkouts,
        'subscribe_cta_clicks': cta_clicks,
        'top_posts': [{'title': p['title'], 'slug': p['slug'], 'views': p.get('views', 0)} for p in top_posts],
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
