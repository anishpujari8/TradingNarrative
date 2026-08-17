"""Email adapter: real Gmail SMTP when configured; mocked logging otherwise.

Mutable module state: EMAIL_LAST_ERROR — always read via `emailer.EMAIL_LAST_ERROR`
(module attribute) so callers see live updates.
"""
import uuid
import asyncio

from config import (JWT_SECRET, FRONTEND_URL, GMAIL_SMTP_USER, GMAIL_SMTP_PASSWORD,
                    EMAIL_FROM_NAME, EMAIL_REPLY_TO, EMAIL_ENABLED, MARKETING_KINDS,
                    ADMIN_NOTIFY_EMAIL, logger)
from db import db
from utils import now_utc, iso

EMAIL_LAST_ERROR = None  # set when an SMTP send fails, surfaced in admin


async def notify_admin_new_subscriber(name: str, email: str, tier: str):
    """Branded admin notification whenever someone new joins (free signup,
    newsletter subscribe, or premium activation). Never raises."""
    from datetime import timedelta
    from html import escape as esc
    try:
        now = now_utc()
        ist = now + timedelta(hours=5, minutes=30)
        when = f"{ist.strftime('%d %b %Y, %I:%M %p')} IST ({now.strftime('%H:%M')} UTC)"
        row = ('<tr><td style="padding:9px 0;font-family:sans-serif;font-size:12px;color:#8a8578;'
               'text-transform:uppercase;letter-spacing:1px;width:120px">{k}</td>'
               '<td style="padding:9px 0;font-size:15px;color:#161a2e;font-weight:600">{v}</td></tr>')
        tier_color = '#1c8570' if 'premium' in tier.lower() else '#8a8578'
        html = f'''
<div style="max-width:560px;margin:0 auto;font-family:Georgia,serif;background:#faf8f3;border:1px solid #e2ddd2;border-radius:12px;overflow:hidden">
  <div style="background:#161a2e;padding:26px 24px;text-align:center">
    <img src="{FRONTEND_URL}/logo.png" alt="The Trading Narrative" width="64" height="64" style="border-radius:50%">
    <p style="color:#1c8570;font-family:monospace;font-size:11px;letter-spacing:3px;text-transform:uppercase;margin:14px 0 4px">The Trading Narrative</p>
    <p style="color:#f2ede7;font-size:19px;margin:0;font-weight:600">New subscriber</p>
  </div>
  <div style="padding:24px 28px">
    <table style="width:100%;border-collapse:collapse;border-bottom:1px solid #e2ddd2">
      {row.format(k='Name', v=esc(name or 'Not provided'))}
      {row.format(k='Email', v=esc(email))}
      {row.format(k='Tier', v=f'<span style="color:{tier_color}">' + esc(tier) + '</span>')}
      {row.format(k='Signed up', v=esc(when))}
    </table>
    <a href="{FRONTEND_URL}/admin" style="display:inline-block;background:#1c8570;color:#ffffff;text-decoration:none;font-family:sans-serif;font-size:14px;font-weight:600;padding:12px 22px;border-radius:8px;margin-top:20px">Open the admin panel</a>
  </div>
  <div style="padding:14px 28px;border-top:1px solid #e2ddd2">
    <p style="font-size:12px;color:#8a8578;font-family:sans-serif;margin:0">Automated notification from thetradingnarrative.com</p>
  </div>
</div>'''
        text = (f'New subscriber on The Trading Narrative\n\n'
                f'Name: {name or "Not provided"}\nEmail: {email}\nTier: {tier}\n'
                f'Signed up: {when}\n\nAdmin panel: {FRONTEND_URL}/admin')
        await log_email(ADMIN_NOTIFY_EMAIL, f'New subscriber: {email} ({tier})', text,
                        'admin_subscriber_alert', html=html)
    except Exception as e:
        logger.warning(f'Admin subscriber notification failed (non-blocking): {str(e)[:150]}')


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
            status = 'failed · logged only'
            logger.warning(f'Gmail SMTP send failed (falling back to log): {err}')
    entry = {
        'id': str(uuid.uuid4()), 'to': to, 'subject': subject, 'body': body,
        'kind': kind, 'provider': provider,
        'sent_at': iso(now_utc()), 'status': status,
    }
    await db.email_logs.insert_one(dict(entry))
    return entry
