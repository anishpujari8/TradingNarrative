"""ElevenLabs narration: chunked synthesis + MongoDB cache (one generation per essay/voice/scope)."""
import asyncio

from bson import Binary

from config import ELEVENLABS_API_KEY, TTS_MODEL, TTS_OUTPUT_FORMAT, TTS_VOICES, logger
from db import db
from utils import now_utc, iso

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


async def get_or_generate_audio(post, voice: str, blocks, scope: str):
    """Return cached MP3 bytes for (post, voice, scope) or synthesize and cache them.
    scope: 'full' (entitled readers) or 'preview' (paywalled preview only)."""
    voice_id = TTS_VOICES[voice]['id']
    key = {'post_slug': post['slug'], 'voice': voice, 'scope': scope}
    cached = await db.audio_cache.find_one(key)
    post_version = post.get('updated_at') or post.get('published_at') or ''
    if cached and cached.get('post_version') == post_version:
        return bytes(cached['audio']), True
    chunks = chunk_text(post['title'], blocks)
    total_chars = sum(len(c) for c in chunks)
    logger.info(f"TTS generate: {post['slug']} voice={voice} scope={scope} chars={total_chars} chunks={len(chunks)}")
    audio = await asyncio.to_thread(_synthesize_sync, chunks, voice_id)
    if len(audio) > 14 * 1024 * 1024:
        # stay under Mongo's 16MB doc limit — serve without caching in the rare oversize case
        logger.warning(f"TTS audio too large to cache ({len(audio)} bytes) for {post['slug']}")
        return audio, False
    await db.audio_cache.update_one(key, {'$set': {
        **key, 'post_version': post_version, 'audio': Binary(audio),
        'bytes': len(audio), 'chars': total_chars, 'created_at': iso(now_utc()),
    }}, upsert=True)
    return audio, False
