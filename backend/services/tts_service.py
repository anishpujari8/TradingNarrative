"""ElevenLabs narration: chunked synthesis + MongoDB cache (one generation per essay/voice/scope)."""
import asyncio

from bson import Binary

from config import ELEVENLABS_API_KEY, PREVIEW_BLOCKS, TTS_ENABLED, TTS_MODEL, TTS_OUTPUT_FORMAT, TTS_VOICES, logger
from db import db
from utils import now_utc, iso, published_query

MAX_CHUNK_CHARS = 4000  # stay well under per-request limits


def _clean_blocks(title, blocks):
    parts = [title] + [(b[3:] if b.startswith('## ') else b) for b in blocks]
    return [p.strip() for p in parts if p.strip()]


def chunk_text(title, blocks):
    """Group paragraphs into chunks of up to MAX_CHUNK_CHARS, splitting on paragraph boundaries."""
    chunks = []
    current = ''
    for p in _clean_blocks(title, blocks):
        if current and len(current) + len(p) + 2 > MAX_CHUNK_CHARS:
            chunks.append(current)
            current = p
        else:
            current = f'{current}\n\n{p}' if current else p
    if current:
        chunks.append(current)
    return chunks


def _synthesize_sync(chunks, voice_id):
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    audio = b''
    for chunk in chunks:
        gen = client.text_to_speech.convert(
            text=chunk,
            voice_id=voice_id,
            model_id=TTS_MODEL,
            output_format=TTS_OUTPUT_FORMAT,
        )
        audio += b''.join(gen)
    return audio


def _valid_cached_audio(cached) -> bool:
    """Guard against corrupt/truncated cache entries: real narration is a sizeable MP3."""
    if not cached or not cached.get('audio'):
        return False
    audio = bytes(cached['audio'])
    if len(audio) < 50 * 1024:
        return False
    return audio[:3] == b'ID3' or (audio[0] == 0xFF and (audio[1] & 0xE0) == 0xE0)


async def get_or_generate_audio(post, voice: str, blocks, scope: str):
    """Return cached MP3 bytes for (post, voice, scope) or synthesize and cache them.
    scope: 'full' (entitled readers) or 'preview' (paywalled preview only)."""
    voice_id = TTS_VOICES[voice]['id']
    key = {'post_slug': post['slug'], 'voice': voice, 'scope': scope}
    cached = await db.audio_cache.find_one(key)
    if cached and not _valid_cached_audio(cached):
        # purge corrupt/truncated entries so they are never served or used as stale fallback
        logger.warning(f"TTS cache: purging corrupt entry for {post['slug']} ({voice}/{scope}, "
                       f"{cached.get('bytes', 0)} bytes)")
        await db.audio_cache.delete_one(key)
        cached = None
    post_version = post.get('updated_at') or post.get('published_at') or ''
    if cached and cached.get('post_version') == post_version:
        return bytes(cached['audio']), True
    chunks = chunk_text(post['title'], blocks)
    total_chars = sum(len(c) for c in chunks)
    logger.info(f"TTS generate: {post['slug']} voice={voice} scope={scope} chars={total_chars} chunks={len(chunks)}")
    try:
        audio = await asyncio.to_thread(_synthesize_sync, chunks, voice_id)
    except Exception as e:
        if cached:
            # RESILIENCE: the essay was edited (cache went stale) but regeneration failed
            # (e.g. out of credits) — a slightly outdated narration beats an error.
            logger.warning(f"TTS regeneration failed for {post['slug']} — serving stale cached audio: {e}")
            return bytes(cached['audio']), True
        raise
    if len(audio) > 14 * 1024 * 1024:
        # stay under Mongo's 16MB doc limit — serve without caching in the rare oversize case
        logger.warning(f"TTS audio too large to cache ({len(audio)} bytes) for {post['slug']}")
        return audio, False
    await db.audio_cache.update_one(key, {'$set': {
        **key, 'post_version': post_version, 'audio': Binary(audio),
        'bytes': len(audio), 'chars': total_chars, 'created_at': iso(now_utc()),
    }}, upsert=True)
    return audio, False


# ---------------------- pre-generation (warm cache so playback is instant) ----------------------

DEFAULT_WARM_VOICE = 'male'  # the player's default voice — the one every first-time listener hears

WARMUP_STATE = {'running': False}  # guards against overlapping warmup runs


async def get_credits():
    """Live ElevenLabs subscription usage (character credits). Returns None if unavailable."""
    if not TTS_ENABLED:
        return None

    def _fetch():
        import requests
        r = requests.get('https://api.elevenlabs.io/v1/user/subscription',
                         headers={'xi-api-key': ELEVENLABS_API_KEY}, timeout=15)
        r.raise_for_status()
        return r.json()

    try:
        data = await asyncio.to_thread(_fetch)
        used = data.get('character_count', 0)
        limit = data.get('character_limit', 0)
        return {'used': used, 'limit': limit, 'remaining': max(0, limit - used),
                'tier': data.get('tier'),
                'resets_at_unix': data.get('next_character_count_reset_unix')}
    except Exception as e:
        logger.warning(f'ElevenLabs credits check failed: {e}')
        return None


async def warm_post_audio(post, voice: str = DEFAULT_WARM_VOICE):
    """Pre-generate the default narration for one published post.
    Only the 'full' scope is warmed: free members hear a byte-clipped 20s preview of the
    same cached MP3, so separate preview audio is no longer generated (saves credits).
    Returns 'generated', 'cached', 'quota' (out of ElevenLabs credits) or 'failed'."""
    if not TTS_ENABLED:
        return 'failed'
    blocks = post.get('content_blocks', [])
    if not blocks:
        return 'failed'
    scopes = [('full', blocks)]
    result = 'cached'
    for scope, blks in scopes:
        try:
            _, from_cache = await get_or_generate_audio(post, voice, blks, scope)
            if not from_cache:
                result = 'generated'
                logger.info(f"TTS warmup: generated {post['slug']} ({scope})")
                await asyncio.sleep(2)  # be gentle with the ElevenLabs API between generations
        except Exception as e:
            if 'quota_exceeded' in str(e):
                logger.warning(f"TTS warmup: ElevenLabs quota exhausted at {post['slug']} ({scope})")
                return 'quota'
            logger.warning(f"TTS warmup failed for {post['slug']} ({scope}): {e}")
            result = 'failed'
    return result


async def warm_all_narrations(initial_delay: int = 15, max_generate: int = 2):
    """Warm the narration cache for every published essay so readers never wait on
    first play. Cached entries are skipped (no extra credits). Startup task + admin-triggered.
    max_generate caps NEW generations per run to protect ElevenLabs credits when many
    essays publish at once — the rest fill in on later runs or on first play."""
    if not TTS_ENABLED or WARMUP_STATE['running']:
        return
    WARMUP_STATE['running'] = True
    try:
        if initial_delay:
            await asyncio.sleep(initial_delay)  # let the app finish booting before doing heavy work
        posts = await db.posts.find(published_query()).sort('published_at', -1).to_list(500)
        logger.info(f'TTS warmup: checking narrations for {len(posts)} published essays')
        counts = {'generated': 0, 'cached': 0, 'failed': 0}
        for post in posts:
            if counts['generated'] >= max_generate:
                logger.info(f"TTS warmup paused: generation cap ({max_generate}/run) reached — "
                            f"remaining essays warm on the next run or on first play.")
                break
            result = await warm_post_audio(post)
            if result == 'quota':
                logger.warning(f"TTS warmup stopped: ElevenLabs credits exhausted "
                               f"({counts['generated']} generated, {counts['cached']} already cached). "
                               f"Top up credits and restart to warm the remaining essays.")
                return
            counts[result] += 1
        logger.info(f"TTS warmup complete: {counts['generated']} generated, "
                    f"{counts['cached']} already cached, {counts['failed']} failed")
    finally:
        WARMUP_STATE['running'] = False
