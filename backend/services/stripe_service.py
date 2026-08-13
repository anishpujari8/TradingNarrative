"""Stripe SDK config + premium activation shared by Stripe and Razorpay flows."""
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

import stripe as stripe_sdk
from emergentintegrations.payments.stripe.checkout import StripeCheckout

from config import STRIPE_API_KEY, IS_SHARED_STRIPE_KEY, FRONTEND_URL, PLANS, AUDIO_UNLOCK_SKU, ADMIN_NOTIFY_EMAIL, logger
from db import db
from utils import now_utc, iso
from services.emailer import log_email


def configure_stripe_sdk():
    stripe_sdk.api_key = STRIPE_API_KEY
    if IS_SHARED_STRIPE_KEY:
        stripe_sdk.api_base = 'https://integrations.emergentagent.com/stripe'
    return stripe_sdk


def stripe_client(webhook_url: Optional[str] = None) -> StripeCheckout:
    return StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url or f'{FRONTEND_URL}/api/webhook/stripe')


async def fulfill_audio_unlock(txn):
    """Idempotently unlock one essay's narration for the buyer (₹45 / $0.50 micro-purchase)."""
    if txn.get('activated'):
        return
    res = await db.payment_transactions.update_one(
        {'session_id': txn['session_id'], 'activated': {'$ne': True}},
        {'$set': {'activated': True, 'updated_at': iso(now_utc())}},
    )
    if res.modified_count == 0:
        return  # another path won the race
    slug = txn.get('audio_slug')
    user = await db.users.find_one({'id': txn['user_id']})
    if not user or not slug:
        return
    await db.users.update_one({'id': user['id']}, {'$addToSet': {'purchased_audio_slugs': slug}})
    post = await db.posts.find_one({'slug': slug})
    title = post['title'] if post else slug
    await db.analytics.insert_one({'id': str(uuid.uuid4()), 'event': 'audio_unlock_purchase',
                                   'path': f'/post/{slug}', 'meta': {'slug': slug, 'title': title},
                                   'user_id': user['id'], 'created_at': iso(now_utc())})
    amount = txn.get('amount')
    currency = (txn.get('currency') or '').upper()
    await log_email(user['email'], 'Your narration is unlocked · The Trading Narrative',
                    f'Thanks for your purchase. The full audio narration of "{title}" is now '
                    f'unlocked on your account, forever.\n\n'
                    f'Amount: {amount} {currency}\n\nEnjoy the listen.', 'audio_unlock_receipt')


async def activate_premium_from_transaction(txn):
    """Idempotently activate premium for the user who paid for this transaction."""
    if txn.get('plan') == AUDIO_UNLOCK_SKU:
        # Per-essay audio micro-purchase, not a subscription
        await fulfill_audio_unlock(txn)
        return
    if txn.get('activated'):
        return
    res = await db.payment_transactions.update_one(
        {'session_id': txn['session_id'], 'activated': {'$ne': True}},
        {'$set': {'activated': True, 'updated_at': iso(now_utc())}},
    )
    if res.modified_count == 0:
        return  # another path won the race
    plan_id = txn['plan']
    plan = PLANS[plan_id]
    user = await db.users.find_one({'id': txn['user_id']})
    if not user:
        return
    existing = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if not existing:
        auto_renew = bool(txn.get('auto_renew'))
        period_end = now_utc() + timedelta(days=plan['period_days'])
        stripe_sub_id = txn.get('stripe_subscription_id')
        rzp_sub_id = txn['session_id'] if txn.get('kind') == 'subscription' else None
        if auto_renew and stripe_sub_id:
            try:
                sdk = configure_stripe_sdk()
                s = sdk.Subscription.retrieve(stripe_sub_id)
                if s.get('current_period_end'):
                    period_end = datetime.fromtimestamp(s['current_period_end'], tz=timezone.utc)
            except Exception as e:
                logger.warning(f'Could not fetch Stripe subscription period end: {e}')
        sub = {
            'id': str(uuid.uuid4()), 'user_id': user['id'], 'plan': plan_id,
            'status': 'active', 'provider': 'stripe',
            'auto_renew': auto_renew,
            'early_bird': bool(txn.get('early_bird')),
            'stripe_session_id': txn['session_id'],
            'stripe_subscription_id': stripe_sub_id,
            'razorpay_subscription_id': rzp_sub_id,
            'gateway': txn.get('provider', 'stripe'),
            'current_period_start': iso(now_utc()),
            'current_period_end': iso(period_end),
            'created_at': iso(now_utc()), 'canceled_at': None,
        }
        await db.subscriptions.insert_one(dict(sub))
    invoice = {
        'id': str(uuid.uuid4()), 'user_id': user['id'],
        'subscription_id': txn['session_id'],
        'number': f"TTN-{now_utc().strftime('%Y%m')}-{secrets.randbelow(9000) + 1000}",
        'amount': txn.get('amount', plan['amount']),
        'currency': txn.get('currency', plan['currency']), 'plan': plan_id,
        'status': 'paid', 'created_at': iso(now_utc()),
    }
    await db.invoices.insert_one(dict(invoice))
    await db.analytics.insert_one({'id': str(uuid.uuid4()), 'event': 'checkout_complete',
                                   'path': '/pricing', 'meta': {'plan': plan_id},
                                   'user_id': user['id'], 'created_at': iso(now_utc())})
    await log_email(user['email'], 'Welcome to Premium · The Trading Narrative',
                    f"Your {plan['label']} pass is active. Enjoy full access.", 'premium_welcome')
    # Admin alert: new paid subscriber (fires once, behind the idempotent activation gate above)
    amount = txn.get('amount', plan.get('amount'))
    currency = (txn.get('currency') or plan.get('currency') or '').upper()
    gateway = txn.get('provider', 'stripe')
    await log_email(
        ADMIN_NOTIFY_EMAIL, 'tradingnarrative email subscriber',
        f"New paid subscriber on The Trading Narrative.\n\n"
        f"Email: {user['email']}\n"
        f"Name: {user.get('name', '')}\n"
        f"Plan: {plan['label']} ({plan_id})\n"
        f"Amount: {amount} {currency}\n"
        f"Provider: {gateway}{' (MOCK payment)' if txn.get('mock') else ''}\n"
        f"Transaction: {txn['session_id']}\n"
        f"Time (UTC): {iso(now_utc())}",
        'admin_subscriber_alert')
