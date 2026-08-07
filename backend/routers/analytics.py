"""Analytics routes: event tracking + admin traffic sources, CSV export, conversion funnel."""
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import Response

from db import db
from utils import now_utc, iso, classify_traffic_source
from security import get_optional_user, get_admin_user
from schemas import TrackIn

router = APIRouter(prefix='/api')


@router.post('/analytics/track')
async def track(body: TrackIn, request: Request, user=Depends(get_optional_user)):
    doc = {
        'id': str(uuid.uuid4()), 'event': body.event, 'path': body.path,
        'meta': body.meta, 'user_id': user['id'] if user else None,
        'sid': body.sid, 'created_at': iso(now_utc()),
    }
    # Traffic source attribution — only on the first pageview of a browser session
    meta = body.meta or {}
    if body.event == 'pageview' and meta.get('first_visit'):
        referrer = (meta.get('referrer') or request.headers.get('referer', '') or '').strip()
        utm_source = (meta.get('utm_source') or '').strip()
        source, ref_host = classify_traffic_source(referrer, utm_source)
        if source:
            doc['source'] = source
            doc['referrer_host'] = ref_host
            if utm_source:
                doc['utm_source'] = utm_source
            if meta.get('utm_medium'):
                doc['utm_medium'] = meta['utm_medium']
            if meta.get('utm_campaign'):
                doc['utm_campaign'] = meta['utm_campaign']
    await db.analytics.insert_one(doc)
    return {'ok': True}


@router.get('/admin/traffic')
async def admin_traffic(admin=Depends(get_admin_user), days: int = Query(30, le=365)):
    since = iso(now_utc() - timedelta(days=days))
    match = {'source': {'$exists': True, '$ne': None}, 'created_at': {'$gte': since}}
    rows = await db.analytics.aggregate([
        {'$match': match},
        {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
    ]).to_list(50)
    total = sum(r['count'] for r in rows) or 0
    sources = [{'source': r['_id'], 'count': r['count'],
                'pct': round(r['count'] * 100 / total, 1) if total else 0} for r in rows]
    referrers = await db.analytics.aggregate([
        {'$match': {**match, 'referrer_host': {'$nin': ['', None]}}},
        {'$group': {'_id': '$referrer_host', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}, {'$limit': 10},
    ]).to_list(10)
    campaigns = await db.analytics.aggregate([
        {'$match': {**match, 'utm_campaign': {'$exists': True, '$nin': ['', None]}}},
        {'$group': {'_id': {'campaign': '$utm_campaign', 'source': '$source'}, 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}, {'$limit': 10},
    ]).to_list(10)
    # weekly trend for the top 5 sources (everything else grouped as 'Other')
    top_sources = [s['source'] for s in sources[:5]]
    docs = await db.analytics.find(match, {'source': 1, 'created_at': 1}).to_list(20000)
    weeks = {}
    for d in docs:
        try:
            dt = datetime.fromisoformat(d['created_at'])
        except Exception:
            continue
        week_start = (dt - timedelta(days=dt.weekday())).date()
        label = week_start.strftime('%b %d')
        key = (week_start, label)
        src = d['source'] if d['source'] in top_sources else 'Other'
        weeks.setdefault(key, {})
        weeks[key][src] = weeks[key].get(src, 0) + 1
    trend_series = list(top_sources)
    if any('Other' in v for v in weeks.values()) and 'Other' not in trend_series:
        trend_series.append('Other')
    trend = []
    for (ws, label) in sorted(weeks.keys()):
        row = {'week': label}
        for s in trend_series:
            row[s] = weeks[(ws, label)].get(s, 0)
        trend.append(row)
    # post attribution: which pages visitors landed on, per source
    pages = await db.analytics.aggregate([
        {'$match': match},
        {'$group': {'_id': {'path': '$path', 'source': '$source'}, 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}, {'$limit': 15},
    ]).to_list(15)
    landing_pages = [{'path': p['_id']['path'] or '/', 'source': p['_id']['source'],
                      'count': p['count']} for p in pages]
    # subscriber growth: weekly new subscribers + cumulative
    all_subs = await db.newsletter_subscribers.find({}, {'created_at': 1}).to_list(20000)
    sub_weeks = {}
    for s in all_subs:
        try:
            dt = datetime.fromisoformat(s['created_at'])
        except Exception:
            continue
        ws = (dt - timedelta(days=dt.weekday())).date()
        sub_weeks[ws] = sub_weeks.get(ws, 0) + 1
    cutoff = (now_utc() - timedelta(days=days)).date()
    running = sum(c for w, c in sub_weeks.items() if w < cutoff)
    subscriber_trend = []
    for ws in sorted(w for w in sub_weeks if w >= cutoff):
        running += sub_weeks[ws]
        subscriber_trend.append({'week': ws.strftime('%b %d'), 'new': sub_weeks[ws], 'total': running})
    return {
        'days': days, 'total_visits': total, 'sources': sources,
        'top_referrers': [{'host': r['_id'], 'count': r['count']} for r in referrers],
        'campaigns': [{'campaign': c['_id']['campaign'], 'source': c['_id']['source'],
                       'count': c['count']} for c in campaigns],
        'trend': trend, 'trend_series': trend_series,
        'landing_pages': landing_pages,
        'subscriber_trend': subscriber_trend,
    }


@router.get('/admin/traffic/export')
async def admin_traffic_export(admin=Depends(get_admin_user), days: int = Query(30, le=365)):
    data = await admin_traffic(admin=admin, days=days)
    import csv as _csv
    import io as _io
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow(['section', 'name', 'source', 'visits', 'share_pct'])
    for s in data['sources']:
        w.writerow(['source', s['source'], '', s['count'], s['pct']])
    for r in data['top_referrers']:
        w.writerow(['referrer', r['host'], '', r['count'], ''])
    for c in data['campaigns']:
        w.writerow(['campaign', c['campaign'], c['source'], c['count'], ''])
    for p in data['landing_pages']:
        w.writerow(['landing_page', p['path'], p['source'], p['count'], ''])
    filename = f'traffic-sources-{days}d-{now_utc().strftime("%Y%m%d")}.csv'
    return Response(content=buf.getvalue(), media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@router.get('/admin/funnel')
async def admin_funnel(admin=Depends(get_admin_user), days: int = Query(30, le=365)):
    """Conversion funnel per traffic source: arrived → viewed pricing → started checkout → went premium.
    Linked via browser session ids; premium matched through the session's user_id."""
    since = iso(now_utc() - timedelta(days=days))
    # 1) attributed sessions: sid -> source
    entries = await db.analytics.find(
        {'source': {'$exists': True, '$ne': None}, 'sid': {'$nin': [None, '']},
         'created_at': {'$gte': since}},
        {'sid': 1, 'source': 1}).to_list(20000)
    sid_source = {}
    for e in entries:
        sid_source.setdefault(e['sid'], e['source'])
    sids = list(sid_source.keys())
    if not sids:
        return {'days': days, 'total_sessions': 0, 'funnel': [], 'overall': None}
    # 2) all events for those sessions
    events = await db.analytics.find(
        {'sid': {'$in': sids}, 'created_at': {'$gte': since}},
        {'sid': 1, 'event': 1, 'path': 1, 'user_id': 1}).to_list(100000)
    sessions = {}
    for ev in events:
        s = sessions.setdefault(ev['sid'], {'pricing': False, 'cta': False, 'user_ids': set()})
        if ev['event'] == 'pageview' and (ev.get('path') or '').startswith('/pricing'):
            s['pricing'] = True
        if ev['event'] == 'subscribe_cta_click':
            s['cta'] = True
        if ev.get('user_id'):
            s['user_ids'].add(ev['user_id'])
    # 3) which users converted (checkout completed) in the window — with plan for the split
    conv_events = await db.analytics.find(
        {'event': 'checkout_complete', 'created_at': {'$gte': since}},
        {'user_id': 1, 'meta': 1}).to_list(10000)
    converted_users = {}
    for c in conv_events:
        if c.get('user_id'):
            converted_users[c['user_id']] = (c.get('meta') or {}).get('plan') or 'monthly'
    # 4) aggregate per source
    per_source = {}
    for sid, src in sid_source.items():
        s = sessions.get(sid, {'pricing': False, 'cta': False, 'user_ids': set()})
        row = per_source.setdefault(src, {'source': src, 'visits': 0, 'pricing_views': 0,
                                          'checkouts_started': 0, 'conversions': 0,
                                          'conversions_monthly': 0, 'conversions_annual': 0})
        row['visits'] += 1
        if s['pricing']:
            row['pricing_views'] += 1
        if s['cta']:
            row['checkouts_started'] += 1
        matched = s['user_ids'] & set(converted_users)
        if matched:
            row['conversions'] += 1
            plan = converted_users[next(iter(matched))]
            if plan == 'annual':
                row['conversions_annual'] += 1
            else:
                row['conversions_monthly'] += 1
    funnel = sorted(per_source.values(), key=lambda r: -r['visits'])
    for r in funnel:
        r['conversion_rate'] = round(r['conversions'] * 100 / r['visits'], 1) if r['visits'] else 0
    overall = {
        'visits': sum(r['visits'] for r in funnel),
        'pricing_views': sum(r['pricing_views'] for r in funnel),
        'checkouts_started': sum(r['checkouts_started'] for r in funnel),
        'conversions': sum(r['conversions'] for r in funnel),
        'conversions_monthly': sum(r['conversions_monthly'] for r in funnel),
        'conversions_annual': sum(r['conversions_annual'] for r in funnel),
    }
    # which essays convert: post views (any session) → did that session's user go premium?
    post_events = await db.analytics.find(
        {'event': 'pageview', 'path': {'$regex': '^/post/'}, 'created_at': {'$gte': since},
         'sid': {'$nin': [None, '']}},
        {'sid': 1, 'path': 1, 'user_id': 1}).to_list(100000)
    post_stats = {}
    sid_users = {sid: s['user_ids'] for sid, s in sessions.items()}
    for ev in post_events:
        slug = ev['path'].split('/post/', 1)[1].split('?')[0]
        stat = post_stats.setdefault(slug, {'slug': slug, 'sessions': set(), 'converted': set()})
        stat['sessions'].add(ev['sid'])
        users = sid_users.get(ev['sid'], set())
        if ev.get('user_id'):
            users = users | {ev['user_id']}
        if users & set(converted_users):
            stat['converted'].add(ev['sid'])
    slugs = list(post_stats.keys())
    titles = {}
    if slugs:
        for p in await db.posts.find({'slug': {'$in': slugs}}, {'slug': 1, 'title': 1}).to_list(200):
            titles[p['slug']] = p['title']
    post_conversions = []
    for s in post_stats.values():
        views, conv = len(s['sessions']), len(s['converted'])
        post_conversions.append({'slug': s['slug'], 'title': titles.get(s['slug'], s['slug']),
                                 'reader_sessions': views, 'conversions': conv,
                                 'rate': round(conv * 100 / views, 1) if views else 0})
    post_conversions.sort(key=lambda x: (-x['conversions'], -x['reader_sessions']))
    return {'days': days, 'total_sessions': len(sids), 'funnel': funnel, 'overall': overall,
            'post_conversions': post_conversions[:10]}
