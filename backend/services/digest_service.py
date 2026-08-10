"""Weekly digest build/send + background loops (Friday autosend, Wednesday briefing reminder)."""
import uuid
import asyncio
from datetime import timedelta
from typing import Optional

from config import CATEGORIES, FRONTEND_URL, EMAIL_ENABLED, GMAIL_SMTP_USER, logger
from db import db
from utils import now_utc, iso, clean, post_summary, published_query
from services import emailer
from services.emailer import log_email


def build_digest_html(posts, top_highlights=None, top_listened=None):
    accent = '#1c8570'
    items = ''
    for p in posts:
        items += f"""
        <tr><td style="padding:0 0 28px 0;">
          <img src="{p['cover_image']}" alt="" width="560" style="width:100%;max-width:560px;border-radius:10px;display:block;" />
          <p style="margin:14px 0 4px;font-family:monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{accent};">{p['category_label']}{' &middot; PREMIUM' if p['tier'] == 'premium' else ''}</p>
          <h2 style="margin:0 0 6px;font-family:Georgia,serif;font-size:22px;line-height:1.3;color:#14181f;">
            <a href="{FRONTEND_URL}/post/{p['slug']}" style="color:#14181f;text-decoration:none;">{p['title']}</a>
          </h2>
          <p style="margin:0 0 8px;font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:#555e6b;">{p['excerpt']}</p>
          <a href="{FRONTEND_URL}/post/{p['slug']}" style="font-family:Arial,sans-serif;font-size:13px;color:{accent};font-weight:bold;text-decoration:none;">Read the essay ({p['read_time']} min) &rarr;</a>
        </td></tr>"""
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f4f1ea;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:32px 16px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:14px;padding:36px;">
        <tr><td style="padding-bottom:26px;border-bottom:1px solid #e8e4da;">
          <span style="display:inline-block;width:10px;height:10px;background:{accent};"></span>
          <span style="font-family:Georgia,serif;font-size:22px;font-weight:bold;color:#14181f;">&nbsp;The Trading Narrative</span>
          <p style="margin:10px 0 0;font-family:monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#8a8577;">The week in narratives</p>
        </td></tr>
        <tr><td style="padding:26px 0 6px;">
          <p style="font-family:Arial,sans-serif;font-size:15px;line-height:1.6;color:#3a4150;margin:0 0 24px;">Here's everything published this week &mdash; the sharpest thinking on markets, tech, and living well.</p>
        </td></tr>
        {items}
        {_highlights_section(top_highlights, accent)}
        {_listens_section(top_listened, accent)}
        <tr><td style="padding-top:8px;border-top:1px solid #e8e4da;">
          <p style="font-family:Arial,sans-serif;font-size:12px;color:#8a8577;margin:16px 0 0;">You're receiving this because you subscribed to The Trading Narrative.<br/>
          <a href="{FRONTEND_URL}" style="color:{accent};">Visit the site</a> &middot; <a href="{FRONTEND_URL}/pricing" style="color:{accent};">Go Premium</a></p>
        </td></tr>
      </table>
    </td></tr></table></body></html>"""


def _highlights_section(top_highlights, accent):
    """Renders the 'most highlighted this week' social-proof block; empty string when no data."""
    if not top_highlights:
        return ''
    rows = ''
    for h in top_highlights:
        rows += f"""
        <div style="border-left:3px solid {accent};padding:2px 0 2px 14px;margin:0 0 16px;">
          <p style="margin:0 0 6px;font-family:Georgia,serif;font-size:16px;font-style:italic;line-height:1.55;color:#14181f;">&ldquo;{h['text']}&rdquo;</p>
          <p style="margin:0;font-family:Arial,sans-serif;font-size:12px;color:#8a8577;">
            {h['count']} readers highlighted this &middot; <a href="{FRONTEND_URL}/post/{h['post_slug']}" style="color:{accent};">{h['post_title']}</a>
          </p>
        </div>"""
    return f"""
        <tr><td style="padding:6px 0 22px;">
          <div style="background:#f7f5f0;border-radius:10px;padding:22px 24px;">
            <p style="margin:0 0 14px;font-family:monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{accent};">Most highlighted this week</p>
            {rows}
          </div>
        </td></tr>"""


def _listens_section(top_listened, accent):
    """Renders the 'most listened this week' narration block; empty string when no data."""
    if not top_listened:
        return ''
    rows = ''
    for i, l in enumerate(top_listened, 1):
        plays = f"{l['count']} play" + ('s' if l['count'] != 1 else '')
        rows += f"""
        <div style="padding:2px 0 2px 0;margin:0 0 14px;">
          <p style="margin:0 0 4px;font-family:Georgia,serif;font-size:16px;line-height:1.5;color:#14181f;">
            <span style="color:{accent};font-weight:bold;">{i}.</span>&nbsp;
            <a href="{FRONTEND_URL}/post/{l['post_slug']}" style="color:#14181f;text-decoration:none;">{l['post_title']}</a>
          </p>
          <p style="margin:0;font-family:Arial,sans-serif;font-size:12px;color:#8a8577;">
            {plays} this week &middot; <a href="{FRONTEND_URL}/post/{l['post_slug']}" style="color:{accent};">Listen to the narration &rarr;</a>
          </p>
        </div>"""
    return f"""
        <tr><td style="padding:6px 0 22px;">
          <div style="background:#f7f5f0;border-radius:10px;padding:22px 24px;">
            <p style="margin:0 0 14px;font-family:monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{accent};">Most listened this week</p>
            {rows}
          </div>
        </td></tr>"""


async def get_week_top_listened(limit: int = 3):
    """Essays whose narration was played the most in the last 7 days."""
    week_ago = iso(now_utc() - timedelta(days=7))
    rows = await db.analytics.aggregate([
        {'$match': {'event': 'narration_listen', 'created_at': {'$gte': week_ago},
                    'meta.slug': {'$ne': None}}},
        {'$group': {'_id': '$meta.slug', 'count': {'$sum': 1}, 'title': {'$last': '$meta.title'}}},
        {'$sort': {'count': -1}},
        {'$limit': limit},
    ]).to_list(limit)
    out = []
    for r in rows:
        # only feature essays that are still published (title fallback from the post itself)
        post = await db.posts.find_one({'slug': r['_id'], **published_query()}, {'title': 1})
        if post:
            out.append({'post_slug': r['_id'], 'post_title': r.get('title') or post['title'],
                        'count': r['count']})
    return out


async def get_week_top_highlights(limit: int = 3):
    """Lines highlighted by 2+ distinct readers in the last 7 days, most-saved first."""
    week_ago = iso(now_utc() - timedelta(days=7))
    rows = await db.highlights.aggregate([
        {'$match': {'created_at': {'$gte': week_ago}}},
        {'$group': {'_id': {'post_slug': '$post_slug', 'post_title': '$post_title', 'text': '$text'},
                    'readers': {'$addToSet': '$user_id'}}},
        {'$project': {'count': {'$size': '$readers'}}},
        {'$match': {'count': {'$gte': 2}}},
        {'$sort': {'count': -1}},
        {'$limit': limit},
    ]).to_list(limit)
    return [{'post_slug': r['_id']['post_slug'], 'post_title': r['_id']['post_title'],
             'text': r['_id']['text'], 'count': r['count']} for r in rows]


async def get_digest_posts():
    week_ago = iso(now_utc() - timedelta(days=7))
    posts = await db.posts.find({**published_query(), 'published_at': {'$gte': week_ago}}).sort('published_at', -1).to_list(20)
    if not posts:
        posts = await db.posts.find(published_query()).sort('published_at', -1).limit(5).to_list(5)
    return [post_summary(clean(p)) for p in posts]


async def do_send_digest(subject: Optional[str] = None, auto: bool = False):
    """Shared digest send — personalised per subscriber's pillar preferences."""
    posts = await get_digest_posts()
    if not posts:
        return None
    subject = subject or f"The Week in Narratives — {now_utc().strftime('%B %d, %Y')}"
    subs = await db.newsletter_subscribers.find({'status': 'subscribed'}).to_list(10000)
    all_cats = list(CATEGORIES.keys())
    top_highlights = await get_week_top_highlights()
    top_listened = await get_week_top_listened()
    html_cache = {}
    sent = 0
    for sub in subs:
        cats = sub.get('categories') or all_cats
        sub_posts = [p for p in posts if p['category'] in cats]
        if not sub_posts:
            continue  # nothing in their chosen pillars this week
        key = tuple(sorted(p['id'] for p in sub_posts))
        if key not in html_cache:
            html_cache[key] = build_digest_html(sub_posts, top_highlights=top_highlights, top_listened=top_listened)
        titles = ', '.join(p['title'] for p in sub_posts[:5])
        await log_email(sub['email'], subject, f'Weekly digest featuring: {titles}', 'digest', html=html_cache[key])
        sent += 1
    issue = {
        'id': str(uuid.uuid4()), 'post_id': None,
        'post_title': f'Weekly digest ({len(posts)} essays · pillar-personalised)',
        'kind': 'digest', 'subject': subject, 'recipients': sent,
        'status': ('sent (gmail)' if EMAIL_ENABLED and not emailer.EMAIL_LAST_ERROR else 'sent (mocked)') + (' · auto' if auto else ''),
        'auto': auto, 'sent_at': iso(now_utc()),
    }
    await db.newsletter_issues.insert_one(dict(issue))
    return issue


async def digest_autosend_loop():
    """Background loop: sends the weekly digest automatically every Friday (UTC),
    at most once per ISO week, when the admin toggle is on."""
    while True:
        try:
            cfg = await db.config.find_one({'key': 'digest_autosend'})
            enabled = bool(cfg and cfg.get('value'))
            now = now_utc()
            if enabled and now.weekday() == 4:  # Friday
                week_key = f'{now.isocalendar().year}-W{now.isocalendar().week}'
                sent = await db.config.find_one({'key': 'digest_autosend_last_week'})
                if not sent or sent.get('value') != week_key:
                    issue = await do_send_digest(auto=True)
                    if issue:
                        await db.config.update_one(
                            {'key': 'digest_autosend_last_week'},
                            {'$set': {'value': week_key, 'sent_at': iso(now)}}, upsert=True)
                        logger.info(f'Weekly digest auto-sent to {issue["recipients"]} subscribers ({week_key})')
        except Exception as e:
            logger.warning(f'Digest autosend loop error: {e}')
        await asyncio.sleep(1800)  # check every 30 minutes


async def do_send_briefing(auto: bool = False):
    """Send the latest published briefing to every newsletter subscriber as a
    high-level summary (title + intro + section headings) with a read-on link."""
    briefing = await db.posts.find_one({**published_query(), 'edition': {'$ne': None}},
                                       sort=[('edition', -1)])
    if not briefing:
        return None
    clean(briefing)
    url = f"{FRONTEND_URL}/post/{briefing['slug']}"
    headings = [b[3:].strip() for b in briefing.get('content_blocks', [])
                if isinstance(b, str) and b.startswith('## ')][:8]
    intro = next((b for b in briefing.get('content_blocks', [])
                  if isinstance(b, str) and not b.startswith('##') and len(b) > 80), briefing.get('excerpt', ''))
    accent = '#1c8570'
    subject = f"Edition #{briefing['edition']} — {briefing['title']}"
    text = (f"{briefing['title']}\n\n{briefing.get('excerpt', '')}\n\nIn this edition:\n"
            + '\n'.join(f'• {h}' for h in headings)
            + f"\n\nRead the full briefing: {url}")
    heads_html = ''.join(f'<li style="margin:6px 0;color:#333">{h}</li>' for h in headings)
    html = (f'<div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;padding:8px">'
            f'<p style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{accent};font-family:sans-serif">'
            f'The Trading Narrative — Wednesday Briefing</p>'
            f'<h1 style="font-size:26px;line-height:1.25;margin:6px 0 14px">{briefing["title"]}</h1>'
            f'<p style="font-size:15px;line-height:1.65;color:#444">{intro[:320]}{"…" if len(intro) > 320 else ""}</p>'
            f'<p style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:#888;font-family:sans-serif;margin:20px 0 6px">In this edition</p>'
            f'<ul style="font-size:15px;line-height:1.5;padding-left:20px;margin:0">{heads_html}</ul>'
            f'<p style="margin:26px 0"><a href="{url}" style="background:{accent};color:#fff;text-decoration:none;'
            f'padding:12px 22px;border-radius:8px;font-family:sans-serif;font-size:14px">Read the full briefing (5 min)</a></p>'
            f'</div>')
    subs = await db.newsletter_subscribers.find({'status': 'subscribed'}).to_list(10000)
    sent = 0
    for sub in subs:
        await log_email(sub['email'], subject, text, 'issue', html=html)
        sent += 1
    issue = {
        'id': str(uuid.uuid4()), 'post_id': briefing['id'], 'post_title': briefing['title'],
        'kind': 'briefing', 'subject': subject, 'recipients': sent,
        'status': ('sent (gmail)' if EMAIL_ENABLED and not emailer.EMAIL_LAST_ERROR else 'sent (mocked)') + (' · auto' if auto else ''),
        'auto': auto, 'sent_at': iso(now_utc()),
    }
    await db.newsletter_issues.insert_one(dict(issue))
    return issue


async def briefing_autosend_loop():
    """Background loop: every Wednesday at 09:30 IST, email the latest published briefing
    to all newsletter subscribers as a high-level summary + link — at most once per ISO week.
    Editions stay free through #6, so this doubles as the growth engine for the list."""
    IST = timedelta(hours=5, minutes=30)
    while True:
        try:
            cfg = await db.config.find_one({'key': 'briefing_autosend'})
            enabled = cfg.get('value') if cfg else True  # on by default per growth plan
            ist_now = now_utc() + IST
            past_930 = ist_now.hour > 9 or (ist_now.hour == 9 and ist_now.minute >= 30)
            if enabled and ist_now.weekday() == 2 and past_930:  # Wednesday, from 09:30 IST
                week_key = f'{ist_now.isocalendar().year}-W{ist_now.isocalendar().week}'
                sent = await db.config.find_one({'key': 'briefing_autosend_last_week'})
                if not sent or sent.get('value') != week_key:
                    issue = await do_send_briefing(auto=True)
                    await db.config.update_one(
                        {'key': 'briefing_autosend_last_week'},
                        {'$set': {'value': week_key, 'sent_at': iso(now_utc())}}, upsert=True)
                    if issue:
                        logger.info(f'Wednesday briefing auto-sent to {issue["recipients"]} subscribers ({week_key})')
        except Exception as e:
            logger.warning(f'Briefing autosend loop error: {e}')
        await asyncio.sleep(600)  # check every 10 minutes so the 9:30 IST window is hit promptly


async def briefing_reminder_loop():
    """Background loop: every Wednesday morning (UTC), if this week's briefing
    hasn't been published yet, email the author a nudge — at most once per week."""
    while True:
        try:
            cfg = await db.config.find_one({'key': 'briefing_reminder'})
            enabled = cfg.get('value') if cfg else True  # on by default
            now = now_utc()
            if enabled and EMAIL_ENABLED and now.weekday() == 2 and now.hour >= 7:  # Wednesday, from 07:00 UTC
                week_key = f'{now.isocalendar().year}-W{now.isocalendar().week}'
                sent = await db.config.find_one({'key': 'briefing_reminder_last_week'})
                if not sent or sent.get('value') != week_key:
                    week_start = iso(now - timedelta(days=now.weekday()))
                    published = await db.posts.find_one({
                        **published_query(), 'edition': {'$ne': None},
                        'published_at': {'$gte': week_start}})
                    if not published:
                        latest = await db.posts.find_one({'edition': {'$ne': None}}, sort=[('edition', -1)])
                        next_ed = (latest.get('edition', 0) + 1) if latest else 1
                        editor_url = f'{FRONTEND_URL}/admin/editor'
                        await log_email(
                            GMAIL_SMTP_USER,
                            f"Reminder: this week's briefing (Edition #{next_ed}) isn't out yet",
                            f"It's Wednesday and Edition #{next_ed} of the weekly briefing hasn't been published.\n\n"
                            f"Open the editor and use the Weekly Briefing Template: {editor_url}",
                            'reminder',
                            html=(f"<p>It's Wednesday and <strong>Edition #{next_ed}</strong> of the weekly briefing "
                                  f"hasn't been published yet.</p>"
                                  f"<p><a href='{editor_url}'>Open the editor</a> and hit "
                                  f"<em>Weekly briefing template</em> — it prefills everything.</p>"))
                    await db.config.update_one({'key': 'briefing_reminder_last_week'},
                                               {'$set': {'value': week_key, 'sent_at': iso(now)}}, upsert=True)
        except Exception as e:
            logger.warning(f'Briefing reminder loop error: {e}')
        await asyncio.sleep(1800)
