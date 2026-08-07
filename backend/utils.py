"""Pure helpers: time, doc cleaning, slugs, post serialization, traffic classification."""
import re
import math
import uuid
from datetime import datetime, timezone, timedelta  # noqa: F401
from typing import List

from seed_data import AUTHOR
from config import CATEGORIES, FRONTEND_URL


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def clean(doc):
    """Strip Mongo _id and return JSON-safe doc."""
    if doc is None:
        return None
    doc.pop('_id', None)
    for k, v in list(doc.items()):
        if isinstance(v, datetime):
            doc[k] = iso(v)
    return doc


def slugify(title: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return s[:80] or str(uuid.uuid4())[:8]


def read_time(blocks: List[str]) -> int:
    words = sum(len(b.split()) for b in blocks)
    return max(1, math.ceil(words / 200))


def post_summary(p):
    return {
        'id': p['id'], 'slug': p['slug'], 'title': p['title'], 'excerpt': p.get('excerpt', ''),
        'category': p['category'], 'category_label': CATEGORIES.get(p['category'], p['category']),
        'tier': p.get('tier', 'free'), 'cover_image': p.get('cover_image', ''),
        'featured': p.get('featured', False), 'read_time': p.get('read_time', 3),
        'tags': p.get('tags', []),
        'author': p.get('author', AUTHOR), 'published_at': p.get('published_at'),
        'status': p.get('status', 'published'), 'views': p.get('views', 0),
        'edition': p.get('edition'),
    }


def published_query():
    now = iso(now_utc())
    return {'$or': [
        {'status': 'published'},
        {'status': 'scheduled', 'publish_at': {'$lte': now}},
    ]}


# ---------------------- traffic source classification ----------------------

TRAFFIC_SOURCE_MAP = {
    'linkedin': 'LinkedIn', 'lnkd.in': 'LinkedIn',
    'instagram': 'Instagram', 'ig.me': 'Instagram', 'l.instagram': 'Instagram',
    't.co': 'X (Twitter)', 'twitter': 'X (Twitter)', 'x.com': 'X (Twitter)',
    'facebook': 'Facebook', 'fb.me': 'Facebook', 'l.facebook': 'Facebook', 'm.facebook': 'Facebook',
    'google': 'Google', 'bing': 'Bing', 'duckduckgo': 'DuckDuckGo', 'yahoo': 'Yahoo',
    'youtube': 'YouTube', 'youtu.be': 'YouTube',
    'reddit': 'Reddit', 'out.reddit': 'Reddit',
    'whatsapp': 'WhatsApp', 'wa.me': 'WhatsApp',
    'telegram': 'Telegram', 't.me': 'Telegram',
    'substack': 'Substack', 'medium': 'Medium',
    'news.ycombinator': 'Hacker News', 'threads.net': 'Threads',
    'pinterest': 'Pinterest', 'quora': 'Quora', 'discord': 'Discord',
    'newsletter': 'Newsletter', 'email': 'Newsletter', 'mail': 'Newsletter',
}


def classify_traffic_source(referrer: str = '', utm_source: str = ''):
    """Return (source_label, referrer_host). source_label is None for internal navigation."""
    from urllib.parse import urlparse
    if utm_source:
        u = utm_source.strip().lower()
        for key, label in TRAFFIC_SOURCE_MAP.items():
            if key in u:
                return label, (urlparse(referrer).netloc.lower() if referrer else '')
        return utm_source.strip().title(), (urlparse(referrer).netloc.lower() if referrer else '')
    if not referrer:
        return 'Direct', ''
    host = urlparse(referrer).netloc.lower()
    if not host:
        return 'Direct', ''
    own_host = urlparse(FRONTEND_URL).netloc.lower() if FRONTEND_URL else ''
    if own_host and host == own_host:
        return None, host  # internal navigation — not a traffic source
    for key, label in TRAFFIC_SOURCE_MAP.items():
        if key in host:
            return label, host
    return 'Other', host
