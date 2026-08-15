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

_OG_VERSION = 'v5'  # bump to invalidate previously cached card designs

_MASCOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'mascots')


def _mascot_medallion(category: str, accent: tuple, size: int = 148) -> Image.Image | None:
    """Circular pillar mascot medallion with an accent ring, or None if unavailable."""
    path = os.path.join(_MASCOT_DIR, f'{category}.webp')
    if not os.path.exists(path):
        return None
    try:
        s = 2  # supersample so the circle mask + ring stay crisp
        d = size * s
        m = Image.open(path).convert('RGB').resize((d, d), Image.LANCZOS)
        mask = Image.new('L', (d, d), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, d - 1, d - 1], fill=255)
        out = Image.new('RGBA', (d, d), (0, 0, 0, 0))
        out.paste(m, (0, 0), mask)
        ring = ImageDraw.Draw(out)
        ring.ellipse([2, 2, d - 3, d - 3], outline=accent + (230,), width=3 * s)
        return out.resize((size, size), Image.LANCZOS)
    except Exception as e:
        logger.debug(f'OG card: mascot medallion skipped: {e}')
        return None


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
        alpha = int(34 * (1 - r / (size / 2)) ** 1.6)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
    img.paste(Image.new('RGB', (size, size), accent), (-260, -300), glow)


# ---------------------------------------------------------------------------
# Pillar signature motifs — each pillar gets its own recognisable background
# illustration, drawn 2x supersampled for smooth anti-aliased lines.
#   Tech & AI          -> circuit-board traces with solder nodes
#   Business & Finance -> ascending market sparkline with data points
#   Personal Growth    -> sunrise arcs radiating from the corner
#   Delivery & Systems -> dashed shipping route with waypoints
# ---------------------------------------------------------------------------

def _bezier(p0, p1, p2, n=120):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def _motif_tech(d: ImageDraw.ImageDraw, s: int, a: tuple) -> None:
    """Circuit traces: right-angle runs ending in solder pads."""
    traces = [
        [(78, 548), (330, 548), (374, 504), (600, 504)],
        [(78, 590), (430, 590), (474, 546), (652, 546)],
        [(700, 92), (980, 92), (1024, 136), (1024, 300)],
        [(1122, 360), (1122, 520), (1078, 564), (900, 564)],
    ]
    for tr in traces:
        d.line([(x * s, y * s) for x, y in tr], fill=a + (64,), width=2 * s)
        for i, (x, y) in enumerate(tr):
            if i in (0, len(tr) - 1):
                d.ellipse([(x - 5) * s, (y - 5) * s, (x + 5) * s, (y + 5) * s],
                          outline=a + (120,), width=2 * s)
                d.ellipse([(x - 2) * s, (y - 2) * s, (x + 2) * s, (y + 2) * s], fill=a + (140,))
            elif 0 < i < len(tr) - 1:
                d.rectangle([(x - 3) * s, (y - 3) * s, (x + 3) * s, (y + 3) * s], fill=a + (90,))


def _motif_finance(d: ImageDraw.ImageDraw, s: int, a: tuple) -> None:
    """Ascending market sparkline with data points and baseline ticks."""
    pts = [(70, 592), (190, 546), (310, 568), (430, 488), (550, 516),
           (670, 440), (790, 464), (910, 380), (1030, 408), (1155, 308)]
    d.line([(x * s, y * s) for x, y in pts], fill=a + (78,), width=3 * s)
    for x, y in pts:
        d.ellipse([(x - 5) * s, (y - 5) * s, (x + 5) * s, (y + 5) * s], fill=a + (34,))
        d.ellipse([(x - 2) * s, (y - 2) * s, (x + 2) * s, (y + 2) * s], fill=a + (150,))
        d.line([(x * s, (y + 12) * s), (x * s, 614 * s)], fill=a + (26,), width=1 * s)


def _motif_growth(d: ImageDraw.ImageDraw, s: int, a: tuple) -> None:
    """Sunrise arcs radiating from the top-right corner + rising sparks."""
    cx, cy = 1185, -55
    for i, r in enumerate(range(110, 560, 74)):
        alpha = max(20, 66 - i * 8)
        d.arc([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
              start=88, end=182, fill=a + (alpha,), width=2 * s)
    for (x, y, r) in [(985, 330, 4), (1075, 415, 3), (880, 245, 3), (1140, 500, 4)]:
        d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=a + (110,))


def _motif_delivery(d: ImageDraw.ImageDraw, s: int, a: tuple) -> None:
    """Dashed shipping route with ringed waypoints and destination pin."""
    path = _bezier((85, 600), (620, 690), (1130, 132), n=140)
    on = True
    for i in range(0, len(path) - 6, 6):
        if on:
            seg = [(x * s, y * s) for x, y in path[i:i + 7]]
            d.line(seg, fill=a + (105,), width=3 * s)
        on = not on
    for t in (0.0, 0.35, 0.7):
        x, y = path[int(t * (len(path) - 1))]
        d.ellipse([(x - 7) * s, (y - 7) * s, (x + 7) * s, (y + 7) * s], outline=a + (150,), width=2 * s)
        d.ellipse([(x - 2) * s, (y - 2) * s, (x + 2) * s, (y + 2) * s], fill=a + (180,))
    # destination: double ring
    x, y = path[-1]
    d.ellipse([(x - 12) * s, (y - 12) * s, (x + 12) * s, (y + 12) * s], outline=a + (150,), width=2 * s)
    d.ellipse([(x - 4) * s, (y - 4) * s, (x + 4) * s, (y + 4) * s], fill=a + (200,))


_MOTIFS = {
    'tech-business': _motif_tech,
    'finance': _motif_finance,
    'lifestyle': _motif_growth,
    'delivery': _motif_delivery,
}


def _motif_briefings(d: ImageDraw.ImageDraw, s: int, a: tuple) -> None:
    """Telegraph wire pulses: the weekly signal arriving on the desk."""
    lines = [
        [(70, 470), (430, 470), (480, 414), (580, 414), (630, 470), (1140, 470)],
        [(70, 540), (520, 540), (570, 486), (680, 486), (740, 592), (800, 540), (1140, 540)],
    ]
    for pts in lines:
        d.line([(x * s, y * s) for x, y in pts], fill=a + (78,), width=3 * s)
    for (x, y) in [(480, 414), (680, 486), (740, 592)]:
        d.ellipse([(x - 6) * s, (y - 6) * s, (x + 6) * s, (y + 6) * s], fill=a + (140,))


def _motif_books(d: ImageDraw.ImageDraw, s: int, a: tuple) -> None:
    """A shelf of book spines with one leaning volume."""
    x0 = 720
    for i, x in enumerate(range(x0, x0 + 4 * 62, 62)):
        y = 330 + (i % 2) * 18
        d.rounded_rectangle([x * s, y * s, (x + 44) * s, 560 * s], radius=6 * s,
                            outline=a + (95,), width=3 * s)
        d.line([(x + 12) * s, (y + 34) * s, (x + 32) * s, (y + 34) * s], fill=a + (80,), width=2 * s)
    d.line([(x0 - 30) * s, 574 * s, 1150 * s, 574 * s], fill=a + (110,), width=3 * s)


def _motif_lounge(d: ImageDraw.ImageDraw, s: int, a: tuple) -> None:
    """Howl arcs: a signal broadcast to the pack."""
    cx, cy = 860, 520
    for i, r in enumerate((110, 180, 250)):
        alpha = 100 - i * 26
        d.arc([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
              start=245, end=340, fill=a + (alpha,), width=3 * s)
    d.ellipse([(cx - 6) * s, (cy - 6) * s, (cx + 6) * s, (cy + 6) * s], fill=a + (150,))


# Section identity cards: Weekly Briefing (falcon), Bookshelf (tortoise), Lounge (wolf).
SECTION_CARDS = {
    'home': {
        'accent': (28, 133, 112),
        'label': 'TRADING · TECH · GROWTH · SYSTEMS',
        'title': 'The Trading Narrative',
        'subtitle': 'Sharp essays and a weekly briefing, written the way a desk reads them.',
        'mascot': 'finance',
        'motif': _motif_finance,
    },
    'briefings': {
        'accent': (193, 73, 83),
        'label': 'THE SERIES',
        'title': 'The Weekly Briefing',
        'subtitle': 'Five things that change how trading desks work, every single week.',
        'mascot': 'briefings',
        'motif': _motif_briefings,
    },
    'books': {
        'accent': (154, 107, 63),
        'label': 'BOOKSHELF',
        'title': "Books Worth a Trader's Time",
        'subtitle': 'A short, honest shelf on trading, risk, and systems that hold up.',
        'mascot': 'books',
        'motif': _motif_books,
    },
    'lounge': {
        'accent': (160, 79, 134),
        'label': 'MEMBERS ONLY',
        'title': 'The Lounge',
        'subtitle': 'Live takes and desk talk with the Premium pack.',
        'mascot': 'lounge',
        'motif': _motif_lounge,
    },
}


def render_section_card(section: str) -> bytes:
    """1200x630 share card for a section identity (falcon / tortoise / wolf)."""
    cfg = SECTION_CARDS[section]
    accent = cfg['accent']
    img = Image.new('RGB', (W, H), BG)
    _vertical_vignette(img)
    _accent_glow(img, accent)

    draw = ImageDraw.Draw(img, 'RGBA')
    _dot_grid(draw, PAD, 210, W - PAD, H - 150)

    # section motif, supersampled like the pillar motifs
    s = 2
    layer = Image.new('RGBA', (W * s, H * s), (0, 0, 0, 0))
    cfg['motif'](ImageDraw.Draw(layer), s, accent)
    layer = layer.resize((W, H), Image.LANCZOS)
    img.paste(layer, (0, 0), layer)
    draw = ImageDraw.Draw(img, 'RGBA')

    mono = _font('IBMPlexMono-SemiBold.ttf', 24)
    mono_sm = _font('IBMPlexMono-SemiBold.ttf', 21)
    sans = _font('Figtree.ttf', 30, weight=500)

    # wordmark eyebrow
    y = 74
    draw.rectangle([PAD, y + 3, PAD + 16, y + 19], fill=accent)
    draw.text((PAD + 32, y), 'THE TRADING NARRATIVE', font=mono, fill=MUTED)

    # section chip
    chip_y = y + 58
    tw = draw.textlength(cfg['label'], font=mono_sm)
    draw.rounded_rectangle([PAD, chip_y, PAD + tw + 44, chip_y + 44], radius=22, fill=accent)
    draw.text((PAD + 22, chip_y + 10), cfg['label'], font=mono_sm, fill=BG_DEEP)

    # title + subtitle (leave room for the large mascot on the right)
    max_w = W - PAD * 2 - 300
    size, lines = 76, []
    while size >= 44:
        serif = _font('EBGaramond-SemiBold.ttf', size, weight=600)
        lines = _wrap(draw, cfg['title'], serif, max_w)
        if len(lines) <= 2:
            break
        size -= 6
    serif = _font('EBGaramond-SemiBold.ttf', size, weight=600)
    ty = chip_y + 96
    for line in lines[:2]:
        draw.text((PAD, ty), line, font=serif, fill=CREAM)
        ty += int(size * 1.2)
    for sub_line in _wrap(draw, cfg['subtitle'], sans, max_w):
        draw.text((PAD, ty + 14), sub_line, font=sans, fill=MUTED)
        ty += 42

    # large mascot medallion, right side
    medallion = _mascot_medallion(cfg['mascot'], accent, size=250)
    if medallion:
        img.paste(medallion, (W - PAD - medallion.width, (H - medallion.height) // 2 - 30), medallion)

    # footer byline
    fy = H - 104
    draw.rectangle([PAD, fy + 8, PAD + 40, fy + 12], fill=accent)
    draw.text((PAD + 56, fy - 8), 'thetradingnarrative.com', font=sans, fill=MUTED)

    # bottom accent strip
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


async def get_or_render_section_card(section: str) -> bytes:
    """Disk-cached section card; keyed by design version."""
    path = os.path.join(CACHE_DIR, f'section-{section}-{_OG_VERSION}.png')
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return f.read()
    from starlette.concurrency import run_in_threadpool
    data = await run_in_threadpool(render_section_card, section)
    with open(path, 'wb') as f:
        f.write(data)
    return data


def _pillar_motif(img: Image.Image, category: str, accent: tuple) -> None:
    """Composite the pillar's signature illustration over the full canvas."""
    motif = _MOTIFS.get(category)
    if not motif:
        return
    s = 2  # supersample for smooth lines
    layer = Image.new('RGBA', (W * s, H * s), (0, 0, 0, 0))
    motif(ImageDraw.Draw(layer), s, accent)
    layer = layer.resize((W, H), Image.LANCZOS)
    img.paste(layer, (0, 0), layer)


def _dot_grid(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    """Subtle dot texture so the canvas never reads flat."""
    for y in range(y0, y1, 34):
        for x in range(x0, x1, 34):
            draw.ellipse([x, y, x + 2, y + 2], fill=(250, 248, 243, 12))


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
    _pillar_motif(img, post.get('category', ''), accent)
    draw = ImageDraw.Draw(img, 'RGBA')

    mono = _font('IBMPlexMono-SemiBold.ttf', 24)
    mono_sm = _font('IBMPlexMono-SemiBold.ttf', 21)
    sans = _font('Figtree.ttf', 27, weight=500)

    # wordmark eyebrow
    y = 74
    draw.rectangle([PAD, y + 3, PAD + 16, y + 19], fill=accent)
    draw.text((PAD + 32, y), 'THE TRADING NARRATIVE', font=mono, fill=MUTED)

    # pillar chip — solid accent pill with dark text for instant recognition
    label = str(CATEGORIES.get(post.get('category', ''), post.get('category', '') or 'Essay')).upper()
    chip_y = y + 58
    tw = draw.textlength(label, font=mono_sm)
    draw.rounded_rectangle([PAD, chip_y, PAD + tw + 44, chip_y + 44], radius=22, fill=accent)
    draw.text((PAD + 22, chip_y + 10), label, font=mono_sm, fill=BG_DEEP)

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

    # pillar mascot medallion (top-right)
    medallion = _mascot_medallion(post.get('category', ''), accent)
    if medallion:
        img.paste(medallion, (W - PAD - medallion.width, 56), medallion)

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
