"""Branded Open Graph share cards (1200x630 PNG), rendered server-side with Pillow.

Every essay gets a consistent, branded preview image for LinkedIn / X / WhatsApp
unfurls: dark navy canvas, pillar-specific accent colour, serif headline, category
chip and the site wordmark. The essay cover image (when reachable) fills the right
panel with a gradient fade so the headline always stays legible.

Pillar accents (recognisable at a glance):
  Tech & AI -> violet | Business & Finance -> brand teal
  Personal Growth -> amber | Delivery & Systems -> steel blue

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
BG_DEEP = (11, 16, 26)     # darker vignette edge
CREAM = (250, 248, 243)    # #faf8f3
TEAL = (43, 160, 138)      # #2ba08a brand default
MUTED = (250, 248, 243, 185)

# pillar accent palette — rich, modern shades that sit well on dark navy
PILLAR_ACCENTS = {
    'tech-business': (129, 122, 244),  # violet — Tech & AI
    'finance': (52, 178, 153),         # brand teal — Business & Finance
    'lifestyle': (222, 158, 66),       # warm amber — Personal Growth
    'delivery': (86, 148, 222),        # steel blue — Delivery & Systems
}

W, H = 1200, 630
PAD = 80

_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts')
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache', 'og_cards')
os.makedirs(CACHE_DIR, exist_ok=True)

_OG_VERSION = 'v2'  # bump to invalidate previously cached card designs


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
    sig = f"{_OG_VERSION}|{post.get('title', '')}|{post.get('updated_at', '')}|{post.get('cover_image', '')}|{post.get('category', '')}"
    return f"{post['slug']}-{hashlib.sha1(sig.encode()).hexdigest()[:12]}.png"


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


def _vertical_vignette(img: Image.Image) -> None:
    """Slightly darker top/bottom edges for depth."""
    grad = Image.new('L', (1, H))
    for y in range(H):
        d = abs(y - H / 2) / (H / 2)          # 0 centre -> 1 edge
        grad.putpixel((0, y), int(90 * (d ** 2.2)))
    grad = grad.resize((W, H))
    img.paste(Image.new('RGB', (W, H), BG_DEEP), (0, 0), grad)


def _accent_glow(img: Image.Image, accent: tuple) -> None:
    """Soft radial accent glow behind the headline (top-left)."""
    size = 900
    glow = Image.new('L', (size, size), 0)
    gd = ImageDraw.Draw(glow)
    cx = cy = size // 2
    for r in range(size // 2, 0, -6):
        alpha = int(26 * (1 - r / (size / 2)) ** 1.6)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
    img.paste(Image.new('RGB', (size, size), accent), (-260, -300), glow)


def _dot_grid(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    """Subtle dot texture so the canvas never reads flat."""
    for y in range(y0, y1, 34):
        for x in range(x0, x1, 34):
            draw.ellipse([x, y, x + 2, y + 2], fill=(250, 248, 243, 14))


def render_card(post: dict, cover_bytes: bytes | None = None) -> bytes:
    """Synchronous Pillow render — call via run_in_threadpool from async routes."""
    img = Image.new('RGB', (W, H), BG)
    accent = PILLAR_ACCENTS.get(post.get('category', ''), TEAL)

    _vertical_vignette(img)
    _accent_glow(img, accent)

    # right cover panel, accent-tinted duotone, gradient fade into the navy canvas
    panel_x = 660
    if cover_bytes:
        try:
            cover = Image.open(io.BytesIO(cover_bytes)).convert('RGB')
            pw, ph = W - panel_x, H
            scale = max(pw / cover.width, ph / cover.height)
            cover = cover.resize((int(cover.width * scale) + 1, int(cover.height * scale) + 1))
            cx = (cover.width - pw) // 2
            cy = (cover.height - ph) // 2
            cover = cover.crop((cx, cy, cx + pw, cy + ph))
            # darken + whisper of accent tint so every pillar's photo feels on-palette
            cover = Image.blend(cover, Image.new('RGB', cover.size, BG), 0.40)
            cover = Image.blend(cover, Image.new('RGB', cover.size, accent), 0.06)
            img.paste(cover, (panel_x, 0))
            # horizontal fade: solid navy at the panel edge -> transparent by ~60%
            fade_w = 420
            fade = Image.new('L', (fade_w, 1), 0)
            for x in range(fade_w):
                t = 1 - x / fade_w
                fade.putpixel((x, 0), int(255 * (t ** 1.35)))
            fade = fade.resize((fade_w, H))
            img.paste(Image.new('RGB', (fade_w, H), BG), (panel_x, 0), fade)
        except Exception as e:
            logger.debug(f'OG card: cover render skipped: {e}')

    draw = ImageDraw.Draw(img, 'RGBA')
    _dot_grid(draw, PAD, 210, panel_x - 40 if cover_bytes else W - PAD, H - 150)

    mono = _font('IBMPlexMono-SemiBold.ttf', 24)
    mono_sm = _font('IBMPlexMono-SemiBold.ttf', 21)
    sans = _font('Figtree.ttf', 27, weight=500)

    # wordmark eyebrow
    y = 74
    draw.rectangle([PAD, y + 3, PAD + 16, y + 19], fill=accent)
    draw.text((PAD + 32, y), 'THE TRADING NARRATIVE', font=mono, fill=MUTED)

    # pillar chip — pill with translucent accent fill + accent text
    label = str(CATEGORIES.get(post.get('category', ''), post.get('category', '') or 'Essay')).upper()
    chip_y = y + 58
    tw = draw.textlength(label, font=mono_sm)
    draw.rounded_rectangle([PAD, chip_y, PAD + tw + 44, chip_y + 44], radius=22,
                           fill=accent + (36,), outline=accent + (110,), width=2)
    draw.text((PAD + 22, chip_y + 10), label, font=mono_sm, fill=accent)

    # headline: adaptive size so long titles always fit (max 4 lines)
    title = post.get('title', 'The Trading Narrative')
    max_w = (panel_x + 60 - PAD) if cover_bytes else W - PAD * 2
    title_top = y + 58 + 86           # below the pillar chip
    title_bottom_limit = H - 150      # keep clear of the byline footer
    size, lines = 68, []
    while size >= 38:
        serif = _font('EBGaramond-SemiBold.ttf', size, weight=600)
        lines = _wrap(draw, title, serif, max_w)
        block_h = len(lines) * int(size * 1.2)
        if len(lines) <= 4 and title_top + block_h <= title_bottom_limit:
            break
        size -= 6
    serif = _font('EBGaramond-SemiBold.ttf', size, weight=600)
    ty = chip_y + 86
    for line in lines[:4]:
        draw.text((PAD, ty), line, font=serif, fill=CREAM)
        ty += int(size * 1.2)

    # footer byline
    fy = H - 104
    draw.rectangle([PAD, fy + 8, PAD + 40, fy + 12], fill=accent)
    read_time = post.get('read_time')
    byline = 'Anish Pujari' + (f'  \u00b7  {read_time} min read' if read_time else '')
    draw.text((PAD + 56, fy - 8), byline, font=sans, fill=MUTED)

    # bottom accent strip: solid accent easing into the canvas on the right
    strip_h = 10
    strip = Image.new('L', (W, 1), 0)
    for x in range(W):
        t = 1 - max(0, (x - W * 0.45)) / (W * 0.55)
        strip.putpixel((x, 0), int(255 * min(1, t) ** 1.4))
    strip = strip.resize((W, strip_h))
    img.paste(Image.new('RGB', (W, strip_h), accent), (0, H - strip_h), strip)

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
