"""Email adapter: real Gmail SMTP when configured; mocked logging otherwise.

Mutable module state: EMAIL_LAST_ERROR — always read via `emailer.EMAIL_LAST_ERROR`
(module attribute) so callers see live updates.
"""
import uuid
import asyncio

from config import (JWT_SECRET, FRONTEND_URL, GMAIL_SMTP_USER, GMAIL_SMTP_PASSWORD,
                    EMAIL_FROM_NAME, EMAIL_REPLY_TO, EMAIL_ENABLED, MARKETING_KINDS, logger)
from db import db
from utils import now_utc, iso

EMAIL_LAST_ERROR = None  # set when an SMTP send fails, surfaced in admin


def _smtp_send(to: str, subject: str, text: str, html: str = None, unsub_url: str = None):
    """Blocking SMTP send — always call via asyncio.to_thread."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f'{EMAIL_FROM_NAME} <{GMAIL_SMTP_USER}>'
    msg['To'] = to
    if EMAIL_REPLY_TO:
        msg['Reply-To'] = EMAIL_REPLY_TO
    if unsub_url:
        msg['List-Unsubscribe'] = f'<{unsub_url}>'
    msg.attach(MIMEText(text or '', 'plain'))
    if html:
        msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
        server.starttls()
        server.login(GMAIL_SMTP_USER, GMAIL_SMTP_PASSWORD)
        server.sendmail(GMAIL_SMTP_USER, [to], msg.as_string())


def unsubscribe_token(email: str) -> str:
    import hmac as _hmac
    import hashlib as _hashlib
    return _hmac.new(JWT_SECRET.encode(), email.strip().lower().encode(), _hashlib.sha256).hexdigest()[:32]


def unsubscribe_url(email: str) -> str:
    from urllib.parse import quote
    return f"{FRONTEND_URL}/api/newsletter/unsubscribe?email={quote(email)}&token={unsubscribe_token(email)}"


async def log_email(to: str, subject: str, body: str, kind: str, html: str = None):
    """Email adapter: real Gmail SMTP when configured; falls back to mocked logging
    on failure so digests/issues never crash the request."""
    global EMAIL_LAST_ERROR
    # one-click unsubscribe footer on marketing emails
    if kind in MARKETING_KINDS:
        u_url = unsubscribe_url(to)
        body = f"{body}\n\n—\nYou're receiving this because you subscribed to The Trading Narrative.\nUnsubscribe: {u_url}"
        footer_html = (f'<hr style="border:none;border-top:1px solid #e5e5e5;margin:28px 0 12px">'
                       f'<p style="font-size:12px;color:#888;font-family:sans-serif">You\'re receiving this because you subscribed to The Trading Narrative. '
                       f'<a href="{u_url}" style="color:#888">Unsubscribe with one click</a>.</p>')
        html = (html or f'<p>{body}</p>') + footer_html
    status = 'sent (mocked)'
    provider = 'mock'
    if EMAIL_ENABLED:
        provider = 'gmail_smtp'
        try:
            await asyncio.to_thread(_smtp_send, to, subject, body, html,
                                    unsubscribe_url(to) if kind in MARKETING_KINDS else None)
            status = 'sent (gmail)'
            EMAIL_LAST_ERROR = None
        except Exception as e:
            err = str(e)[:200]
            EMAIL_LAST_ERROR = err
            status = 'failed — logged only'
            logger.warning(f'Gmail SMTP send failed (falling back to log): {err}')
    entry = {
        'id': str(uuid.uuid4()), 'to': to, 'subject': subject, 'body': body,
        'kind': kind, 'provider': provider,
        'sent_at': iso(now_utc()), 'status': status,
    }
    await db.email_logs.insert_one(dict(entry))
    return entry
