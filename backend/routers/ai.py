"""AI features powered by Gemini (via the Emergent universal LLM key):
- Admin writing assistant (draft / polish / expand) with streaming output
- "Ask this essay" reader chat, grounded in the essay content (paywall-aware)
"""
import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import AI_ENABLED, AI_PROVIDER, AI_MODEL, EMERGENT_LLM_KEY, PREVIEW_BLOCKS, logger
from db import db
from utils import published_query
from security import get_admin_user, get_optional_user, is_entitled

router = APIRouter(prefix='/api')

SSE_HEADERS = {'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}

AUTHOR_VOICE = (
    "You write for The Trading Narrative, the publication of Anish Pujari — a senior ETRM/CTRM "
    "product manager who spent 12+ years inside commodity trading floors. The voice is "
    "operator-grade and plainspoken: first-person, concrete, sceptical of press-release language, "
    "always anchored in how a trading desk actually works. Short paragraphs. No hype, no emojis."
)

FORMAT_RULES = (
    "FORMAT RULES: Return plain text only (no markdown bold/italics/lists). Separate paragraphs "
    "with a single blank line. Section headings, if needed, must be on their own line starting "
    "with '## '. Do not add a title line unless explicitly asked."
)

ASSIST_MODES = {
    'draft': (
        f"{AUTHOR_VOICE}\nWrite a complete essay draft from the brief or notes the author gives "
        f"you. Aim for 600-1000 words with 2-4 '## ' section headings. {FORMAT_RULES}"
    ),
    'polish': (
        f"{AUTHOR_VOICE}\nPolish the draft you are given: fix grammar, tighten sentences, improve "
        f"flow and clarity — but preserve the author's voice, structure, headings and meaning. "
        f"Return the full polished text. {FORMAT_RULES}"
    ),
    'expand': (
        f"{AUTHOR_VOICE}\nExpand the draft you are given: deepen the argument with concrete "
        f"examples, mechanics and consequences, keeping the existing structure and voice. Return "
        f"the full expanded text. {FORMAT_RULES}"
    ),
}


class AssistIn(BaseModel):
    mode: str = Field(pattern='^(draft|polish|expand)$')
    text: str = Field(min_length=1, max_length=40000)
    instructions: Optional[str] = Field(default=None, max_length=2000)


class AskHistoryItem(BaseModel):
    role: str = Field(pattern='^(user|assistant)$')
    text: str = Field(max_length=4000)


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: List[AskHistoryItem] = Field(default_factory=list, max_length=6)


def _sse(payload: dict) -> str:
    return f'data: {json.dumps(payload)}\n\n'


async def _stream_llm(system_message: str, user_text: str):
    """Yield SSE events with text deltas from Gemini; one clean error event on failure."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
    chat = (LlmChat(api_key=EMERGENT_LLM_KEY, session_id=str(uuid.uuid4()),
                    system_message=system_message)
            .with_model(AI_PROVIDER, AI_MODEL))
    try:
        async for ev in chat.stream_message(UserMessage(text=user_text)):
            if isinstance(ev, TextDelta):
                yield _sse({'delta': ev.content})
            elif isinstance(ev, StreamDone):
                break
        yield _sse({'done': True})
    except Exception as e:
        logger.error(f'AI stream failed: {e}')
        yield _sse({'error': 'The assistant is temporarily unavailable. Please try again.'})


@router.post('/admin/ai/assist')
async def ai_assist(body: AssistIn, admin=Depends(get_admin_user)):
    """Admin writing assistant: draft from a brief, or polish/expand an existing draft."""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail='AI assistant is not configured')
    prompt = body.text
    if body.instructions:
        prompt = f'{body.text}\n\nADDITIONAL INSTRUCTIONS FROM THE AUTHOR: {body.instructions}'
    if body.mode == 'draft':
        prompt = f'Write an essay draft from this brief / these notes:\n\n{prompt}'
    else:
        verb = 'Polish' if body.mode == 'polish' else 'Expand'
        prompt = f'{verb} this draft:\n\n{prompt}'
    return StreamingResponse(_stream_llm(ASSIST_MODES[body.mode], prompt),
                             media_type='text/event-stream', headers=SSE_HEADERS)


@router.post('/posts/{slug}/ask')
async def ask_essay(slug: str, body: AskIn, user=Depends(get_optional_user)):
    """Grounded Q&A about one essay. SERVER-SIDE PAYWALL: non-entitled readers of premium
    essays get answers grounded only in the free preview."""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail='Essay chat is not configured')
    if not user:
        # ACCESS MODEL: essays (and essay chat) are for signed-in readers only
        raise HTTPException(status_code=401, detail='Sign in to ask this essay questions.')
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    blocks = post.get('content_blocks', [])
    scope_note = ''
    if post.get('tier') == 'premium' and not await is_entitled(user):
        blocks = blocks[:PREVIEW_BLOCKS]
        scope_note = ("\nNOTE: Only the FREE PREVIEW of this premium essay is available to this "
                      "reader. If their question is likely answered later in the essay, say so "
                      "briefly and suggest subscribing to read the full essay — do not guess.")
    essay = '\n\n'.join(blocks)[:30000]
    system = (
        "You are the reader assistant for The Trading Narrative. Answer questions about the essay "
        "below, grounded ONLY in its content. Be concise (2-5 short sentences unless asked for "
        "more). If the essay does not answer the question, say so plainly — never invent facts. "
        "Plain text only, no markdown."
        f"{scope_note}\n\nESSAY TITLE: {post['title']}\n\nESSAY CONTENT:\n{essay}"
    )
    convo = ''
    for h in body.history[-6:]:
        speaker = 'Reader' if h.role == 'user' else 'Assistant'
        convo += f'{speaker}: {h.text}\n'
    user_text = (f'Previous conversation:\n{convo}\n' if convo else '') + f'Reader question: {body.question}'
    return StreamingResponse(_stream_llm(system, user_text),
                             media_type='text/event-stream', headers=SSE_HEADERS)


@router.get('/ai/status')
async def ai_status():
    return {'enabled': AI_ENABLED, 'model': AI_MODEL if AI_ENABLED else None}
