"""Branded Open Graph share cards (1200x630 PNG), rendered server-side with Pillow.

Every essay gets a consistent, branded preview image for LinkedIn / X / WhatsApp
unfurls: dark navy canvas, teal accent, serif headline, category eyebrow and the
site wordmark. The essay cover image (when reachable) fills the right panel with
a gradient fade so the headline always stays legible.

Cards are cached on disk keyed by (slug + title + updated_at + cover_image), so
they regenerate automatically when an essay is edited and cost nothing on
subsequent requests. No external service or API key involved.
"""
import hashlib
import io
import os

import httpx
from PIL import Image, ImageDraw, ImageFont

from config import CATEGORIES, logger

# brand tokens (mirrors the frontend share-card canvas in ShareBar.js)
BG = (16, 22, 35)          # #101623 dark navy
CREAM = (250, 248, 243)    # #faf8f3
TEAL = (43, 160, 138)      # #2ba08a
MUTED = (250, 248, 243, 190)

W, H = 1200, 630
PAD = 80

_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts')
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache', 'og_cards')
os.makedirs(CACHE_DIR, exist_ok=True)


def _font(file: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(os.path.join(_FONT_DIR, file), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])  # variable fonts (EB Garamond / Figtree)
        except Exception:
            pass  # static font, single weight
    return f


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    lines, line = [], ''
    for word in text.split():
        test = f'{line} {word}'.strip()
        if draw.textlength(test, font=font) > max_width and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def cache_key(post: dict) -> str:
    sig = f"{post.get('title', '')}|{post.get('updated_at', '')}|{post.get('cover_image', '')}"
    return f"{post['slug']}-{hashlib.sha1(sig.encode()).hexdigest()[:12]}.png"


def cached_card_path(post: dict) -> str | None:
    path = os.path.join(CACHE_DIR, cache_key(post))
    return path if os.path.exists(path) else None


async def fetch_cover(url: str) -> bytes | None:
    """Best-effort cover fetch; the card renders fine without it."""
    if not url or not url.startswith('http'):
        return None
    try:
        async with httpx.AsyncClient(timeout=6, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code == 200 and r.headers.get('content-type', '').startswith('image'):
                return r.content
    except Exception as e:
        logger.debug(f'OG card: cover fetch failed for {url}: {e}')
    return None


def render_card(post: dict, cover_bytes: bytes | None = None) -> bytes:
    """Synchronous Pillow render — call via run_in_threadpool from async routes."""
    img = Image.new('RGB', (W, H), BG)

    # right cover panel with gradient fade into the navy canvas
    if cover_bytes:
        try:
            cover = Image.open(io.BytesIO(cover_bytes)).convert('RGB')
            panel_x = 640
            pw, ph = W - panel_x, H
            scale = max(pw / cover.width, ph / cover.height)
            cover = cover.resize((int(cover.width * scale) + 1, int(cover.height * scale) + 1))
            cx = (cover.width - pw) // 2
            cy = (cover.height - ph) // 2
            cover = cover.crop((cx, cy, cx + pw, cy + ph))
            # darken so the panel never fights the headline
            cover = Image.blend(cover, Image.new('RGB', cover.size, BG), 0.42)
            img.paste(cover, (panel_x, 0))
            # horizontal fade: solid navy at the panel edge -> transparent by ~65%
            fade_w = 380
            fade = Image.new('L', (fade_w, 1), 0)
            for x in range(fade_w):
                fade.putpixel((x, 0), int(255 * (1 - x / fade_w)))
            fade = fade.resize((fade_w, H))
            img.paste(Image.new('RGB', (fade_w, H), BG), (panel_x, 0), fade)
        except Exception as e:
            logger.debug(f'OG card: cover render skipped: {e}')

    draw = ImageDraw.Draw(img, 'RGBA')

    mono = _font('IBMPlexMono-SemiBold.ttf', 25)
    sans = _font('Figtree.ttf', 27, weight=500)

    # wordmark eyebrow
    y = 78
    draw.rectangle([PAD, y + 4, PAD + 16, y + 20], fill=TEAL)
    draw.text((PAD + 32, y), 'THE TRADING NARRATIVE', font=mono, fill=MUTED)

    # category eyebrow
    label = CATEGORIES.get(post.get('category', ''), post.get('category', '') or 'Essay')
    draw.text((PAD, y + 62), str(label).upper(), font=mono, fill=TEAL)

    # headline: adaptive size so long titles always fit (max 4 lines)
    title = post.get('title', 'The Trading Narrative')
    max_w = 720 - PAD if cover_bytes else W - PAD * 2
    size, lines = 64, []
    while size >= 40:
        serif = _font('EBGaramond-SemiBold.ttf', size, weight=600)
        lines = _wrap(draw, title, serif, max_w)
        if len(lines) <= 4:
            break
        size -= 6
    serif = _font('EBGaramond-SemiBold.ttf', size, weight=600)
    ty = y + 128
    for line in lines[:4]:
        draw.text((PAD, ty), line, font=serif, fill=CREAM)
        ty += int(size * 1.22)

    # footer byline
    fy = H - 108
    draw.rectangle([PAD, fy + 8, PAD + 40, fy + 12], fill=TEAL)
    read_time = post.get('read_time')
    byline = 'Anish Pujari' + (f'  \u00b7  {read_time} min read' if read_time else '')
    draw.text((PAD + 56, fy - 8), byline, font=sans, fill=MUTED)

    # bottom accent strip
    draw.rectangle([0, H - 10, W, H], fill=TEAL)

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return buf.getvalue()


async def get_or_render_card(post: dict) -> bytes:
    """Disk-cached card bytes for a post; renders (and caches) on first request."""
    path = os.path.join(CACHE_DIR, cache_key(post))
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return f.read()
    cover_bytes = await fetch_cover(post.get('cover_image', ''))
    from starlette.concurrency import run_in_threadpool
    data = await run_in_threadpool(render_card, post, cover_bytes)
    # prune stale versions of this slug (edited essays) before writing the new one
    try:
        prefix = f"{post['slug']}-"
        for fn in os.listdir(CACHE_DIR):
            if fn.startswith(prefix):
                os.remove(os.path.join(CACHE_DIR, fn))
    except OSError as e:
        logger.debug(f'OG card: cache prune skipped: {e}')
    with open(path, 'wb') as f:
        f.write(data)
    return data
