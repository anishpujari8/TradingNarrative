"""Newsletter routes: subscribe, unsubscribe, preferences, digest ops, autosend + reminder toggles."""
import uuid

from fastapi import APIRouter, HTTPException, Depends, Query

from config import CATEGORIES, FRONTEND_URL, GMAIL_SMTP_USER
from db import db
from utils import now_utc, iso, clean
from security import get_current_user, get_admin_user
from schemas import NewsletterIn, NewsletterPrefsIn, DigestSendIn, AutosendIn
from services.emailer import log_email, unsubscribe_token
from services.digest_service import build_digest_html, get_digest_posts, do_send_digest

router = APIRouter(prefix='/api')


@router.post('/newsletter/subscribe')
async def newsletter_subscribe(body: NewsletterIn):
    email = body.email.lower()
    existing = await db.newsletter_subscribers.find_one({'email': email})
    if existing:
        return {'ok': True, 'message': "You're already subscribed!", 'already': True}
    await db.newsletter_subscribers.insert_one({
        'id': str(uuid.uuid4()), 'email': email, 'source': body.source,
        'status': 'subscribed', 'created_at': iso(now_utc()),
    })
    await log_email(email, 'Welcome to The Trading Narrative',
                    'Thanks for subscribing! Expect sharp insights on tech, markets, and living well.', 'welcome')
    await db.analytics.insert_one({'id': str(uuid.uuid4()), 'event': 'newsletter_subscribe',
                                   'path': body.source, 'meta': {}, 'user_id': None,
                                   'created_at': iso(now_utc())})
    return {'ok': True, 'message': "You're in! Check your inbox for a welcome note.", 'already': False}


@router.get('/newsletter/unsubscribe')
async def newsletter_unsubscribe(email: str = Query(...), token: str = Query(...)):
    from fastapi.responses import HTMLResponse
    ok = token == unsubscribe_token(email)
    if ok:
        await db.newsletter_subscribers.update_one(
            {'email': email.strip().lower()}, {'$set': {'status': 'unsubscribed',
                                                        'unsubscribed_at': iso(now_utc())}})
    heading = "You're unsubscribed" if ok else "That link didn't work"
    message = ("You won't receive the weekly digest or new-essay emails anymore. "
               "Changed your mind? You can re-subscribe any time from your account page.") if ok else \
              ("This unsubscribe link is invalid or expired. "
               "You can manage email preferences from your account page instead.")
    page = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{heading} — The Trading Narrative</title></head>
<body style='margin:0;background:#faf9f7;font-family:Georgia,serif;color:#1a1a1a'>
<div style='max-width:480px;margin:12vh auto;padding:40px;background:#fff;border:1px solid #e8e6e1;border-radius:16px;text-align:center'>
<div style='font-size:13px;letter-spacing:2px;text-transform:uppercase;color:#2a7d6c;font-family:monospace'>The Trading Narrative</div>
<h1 style='font-size:28px;margin:18px 0 12px'>{heading}</h1>
<p style='font-size:15px;line-height:1.6;color:#555'>{message}</p>
<a href='{FRONTEND_URL}' style='display:inline-block;margin-top:18px;padding:12px 28px;background:#2a7d6c;color:#fff;text-decoration:none;border-radius:8px;font-family:sans-serif;font-size:14px'>Back to the essays</a>
</div></body></html>"""
    return HTMLResponse(content=page, status_code=200 if ok else 400)


@router.get('/newsletter/my-preferences')
async def my_newsletter_prefs(user=Depends(get_current_user)):
    sub = await db.newsletter_subscribers.find_one({'email': user['email']})
    if not sub:
        return {'subscribed': False, 'categories': list(CATEGORIES.keys())}
    return {'subscribed': sub.get('status') == 'subscribed',
            'categories': sub.get('categories', list(CATEGORIES.keys()))}


@router.post('/newsletter/my-preferences')
async def set_newsletter_prefs(body: NewsletterPrefsIn, user=Depends(get_current_user)):
    cats = [c for c in body.categories if c in CATEGORIES] or list(CATEGORIES.keys())
    sub = await db.newsletter_subscribers.find_one({'email': user['email']})
    if not sub:
        await db.newsletter_subscribers.insert_one({
            'id': str(uuid.uuid4()), 'email': user['email'], 'source': 'account',
            'status': 'subscribed' if body.subscribed else 'unsubscribed',
            'categories': cats, 'created_at': iso(now_utc()),
        })
    else:
        await db.newsletter_subscribers.update_one({'email': user['email']}, {'$set': {
            'status': 'subscribed' if body.subscribed else 'unsubscribed',
            'categories': cats,
        }})
    return {'ok': True, 'subscribed': body.subscribed, 'categories': cats}


# ---------------------- weekly digest ----------------------

@router.get('/admin/newsletter/digest-preview')
async def digest_preview(admin=Depends(get_admin_user)):
    posts = await get_digest_posts()
    subject = f"The Week in Narratives — {now_utc().strftime('%B %d, %Y')}"
    return {'subject': subject, 'post_count': len(posts), 'posts': posts,
            'html': build_digest_html(posts)}


@router.post('/admin/newsletter/send-digest')
async def send_digest(body: DigestSendIn, admin=Depends(get_admin_user)):
    issue = await do_send_digest(subject=body.subject, auto=False)
    if not issue:
        raise HTTPException(status_code=400, detail='No published posts to include')
    return clean(issue)


@router.post('/admin/newsletter/send-digest-preview')
async def send_digest_preview(body: DigestSendIn, admin=Depends(get_admin_user)):
    """Send the full weekly digest to the admin only — a dry run before it reaches subscribers."""
    posts = await get_digest_posts()
    if not posts:
        raise HTTPException(status_code=400, detail='No published posts to include')
    subject = body.subject or f"[PREVIEW] The Week in Narratives — {now_utc().strftime('%B %d, %Y')}"
    to = GMAIL_SMTP_USER or admin['email']
    titles = ', '.join(p['title'] for p in posts[:5])
    entry = await log_email(to, subject, f'Weekly digest preview featuring: {titles}', 'digest',
                            html=build_digest_html(posts))
    return {'ok': True, 'to': to, 'status': entry['status'], 'posts': len(posts)}


# ---------------------- weekly digest autosend (every Friday) ----------------------

@router.get('/admin/newsletter/autosend')
async def get_autosend(admin=Depends(get_admin_user)):
    cfg = await db.config.find_one({'key': 'digest_autosend'})
    last = await db.config.find_one({'key': 'digest_autosend_last_week'})
    return {'enabled': bool(cfg and cfg.get('value')),
            'last_auto_send': last.get('sent_at') if last else None}


@router.post('/admin/newsletter/autosend')
async def set_autosend(body: AutosendIn, admin=Depends(get_admin_user)):
    await db.config.update_one({'key': 'digest_autosend'},
                               {'$set': {'value': body.enabled}}, upsert=True)
    return {'ok': True, 'enabled': body.enabled}


# ---------------------- Wednesday briefing reminder ----------------------

@router.get('/admin/newsletter/briefing-reminder')
async def get_briefing_reminder(admin=Depends(get_admin_user)):
    cfg = await db.config.find_one({'key': 'briefing_reminder'})
    last = await db.config.find_one({'key': 'briefing_reminder_last_week'})
    return {'enabled': cfg.get('value') if cfg else True,
            'last_checked': last.get('sent_at') if last else None}


@router.post('/admin/newsletter/briefing-reminder')
async def set_briefing_reminder(body: AutosendIn, admin=Depends(get_admin_user)):
    await db.config.update_one({'key': 'briefing_reminder'},
                               {'$set': {'value': body.enabled}}, upsert=True)
    return {'ok': True, 'enabled': body.enabled}
