"""Stripe billing routes: config, checkout, payment status, webhook, cancel, subscription, invoices."""
import uuid
import asyncio
import random
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends, Request

from config import (MOCK_BILLING, AUTO_RENEW, IS_SHARED_STRIPE_KEY, FRONTEND_URL,
                    RAZORPAY_ENABLED, RAZORPAY_KEY_ID, PLANS, AUDIO_UNLOCK_SKU,
                    AUDIO_UNLOCK_PRICE_USD, logger)
from db import db
from utils import now_utc, iso, clean, published_query, has_free_audio, owns_audio, premium_audio_only
from security import get_current_user, is_entitled
from schemas import CheckoutIn, AudioCheckoutIn
from services import razorpay_service as rzp
from services.stripe_service import stripe_client, configure_stripe_sdk, activate_premium_from_transaction
from services.emailer import log_email
from emergentintegrations.payments.stripe.checkout import CheckoutSessionRequest

router = APIRouter(prefix='/api')


@router.get('/billing/config')
async def billing_config():
    await rzp.maybe_reprobe_razorpay()
    return {'mock_mode': MOCK_BILLING, 'auto_renew': AUTO_RENEW,
            'razorpay_enabled': RAZORPAY_ENABLED, 'razorpay_key_id': RAZORPAY_KEY_ID or None,
            'razorpay_autopay': rzp.RAZORPAY_SUBS_ENABLED,
            'plans': list(PLANS.values())}


@router.post('/billing/checkout')
async def checkout(body: CheckoutIn, user=Depends(get_current_user)):
    if body.plan not in PLANS:
        raise HTTPException(status_code=400, detail='Invalid plan')
    existing = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail='You already have an active subscription')
    plan = PLANS[body.plan]

    if MOCK_BILLING:
        # MOCKED fallback path (MOCK_BILLING=true)
        period_days = plan['period_days']
        sub = {
            'id': str(uuid.uuid4()), 'user_id': user['id'], 'plan': body.plan,
            'status': 'active', 'provider': 'mock',
            'current_period_start': iso(now_utc()),
            'current_period_end': iso(now_utc() + timedelta(days=period_days)),
            'created_at': iso(now_utc()), 'canceled_at': None,
        }
        await db.subscriptions.insert_one(dict(sub))
        invoice = {
            'id': str(uuid.uuid4()), 'user_id': user['id'], 'subscription_id': sub['id'],
            'number': f"TTN-{now_utc().strftime('%Y%m')}-{random.randint(1000, 9999)}",
            'amount': plan['amount'], 'currency': plan['currency'], 'plan': body.plan,
            'status': 'paid', 'created_at': iso(now_utc()),
        }
        await db.invoices.insert_one(dict(invoice))
        await log_email(user['email'], 'Welcome to Premium · The Trading Narrative',
                        f"Your {plan['label']} subscription is active.", 'premium_welcome')
        return {'ok': True, 'mock': True, 'subscription': clean(sub), 'invoice': clean(invoice)}

    # REAL STRIPE CHECKOUT (test mode)
    origin = (body.origin_url or FRONTEND_URL).rstrip('/')
    success_url = f'{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = f'{origin}/payment/cancel'
    metadata = {'user_id': user['id'], 'plan': body.plan, 'app': 'trading-narrative'}
    try:
        if AUTO_RENEW:
            # TRUE AUTO-RENEWING SUBSCRIPTION (user's own Stripe key)
            sdk = configure_stripe_sdk()
            session_obj = sdk.checkout.Session.create(
                mode='subscription',
                line_items=[{
                    'price_data': {
                        'currency': plan['currency'],
                        'unit_amount': int(round(plan['amount'] * 100)),
                        'recurring': {'interval': plan['interval']},
                        'product_data': {'name': f"The Trading Narrative Premium — {plan['label']}"},
                    },
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
            session_url, session_id = session_obj.url, session_obj.id
        else:
            # One-time timed pass (shared Emergent test key — Stripe-side cancel API unavailable)
            checkout_req = CheckoutSessionRequest(
                amount=float(plan['amount']),
                currency=plan['currency'],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
            session = await stripe_client().create_checkout_session(checkout_req)
            session_url, session_id = session.url, session.session_id
    except Exception as e:
        logger.error(f'Stripe checkout creation failed: {e}')
        raise HTTPException(status_code=502, detail='Could not start Stripe checkout. Please try again.')
    await db.payment_transactions.insert_one({
        'session_id': session_id, 'user_id': user['id'], 'plan': body.plan,
        'amount': plan['amount'], 'currency': plan['currency'],
        'auto_renew': AUTO_RENEW,
        'status': 'initiated', 'payment_status': 'pending', 'activated': False,
        'created_at': iso(now_utc()), 'updated_at': iso(now_utc()),
    })
    return {'ok': True, 'mock': False, 'checkout_url': session_url, 'session_id': session_id}


async def _validate_audio_purchase(user, slug: str):
    """Shared guardrails for the ₹45 / $0.50 per-essay narration unlock."""
    post = await db.posts.find_one({'slug': slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Essay not found')
    if await is_entitled(user):
        raise HTTPException(status_code=400, detail='Premium members already enjoy full narrations')
    if premium_audio_only(post):
        raise HTTPException(status_code=400, detail='This narration is exclusive to Premium members')
    if has_free_audio(post):
        raise HTTPException(status_code=400, detail='This narration is already free to listen')
    if owns_audio(user, slug):
        raise HTTPException(status_code=400, detail='You already own this narration')
    return post


@router.post('/billing/audio/checkout')
async def audio_checkout(body: AudioCheckoutIn, user=Depends(get_current_user)):
    """One-time Stripe purchase ($0.50) unlocking a single essay's full narration."""
    post = await _validate_audio_purchase(user, body.slug)
    origin = (body.origin_url or FRONTEND_URL).rstrip('/')
    success_url = f'{origin}/post/{body.slug}?audio_session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = f'{origin}/post/{body.slug}'
    metadata = {'user_id': user['id'], 'sku': AUDIO_UNLOCK_SKU, 'slug': body.slug,
                'app': 'trading-narrative'}
    if MOCK_BILLING:
        # MOCKED fallback path — unlock instantly (no gateway without keys)
        await db.users.update_one({'id': user['id']},
                                  {'$addToSet': {'purchased_audio_slugs': body.slug}})
        return {'ok': True, 'mock': True}
    try:
        if not IS_SHARED_STRIPE_KEY:
            # One-time payment on the user's own Stripe key
            sdk = configure_stripe_sdk()
            session_obj = sdk.checkout.Session.create(
                mode='payment',
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(round(AUDIO_UNLOCK_PRICE_USD * 100)),
                        'product_data': {'name': f"Audio narration — {post['title'][:90]}"},
                    },
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
            session_url, session_id = session_obj.url, session_obj.id
        else:
            checkout_req = CheckoutSessionRequest(
                amount=AUDIO_UNLOCK_PRICE_USD, currency='usd',
                success_url=success_url, cancel_url=cancel_url, metadata=metadata,
            )
            session = await stripe_client().create_checkout_session(checkout_req)
            session_url, session_id = session.url, session.session_id
    except Exception as e:
        logger.error(f'Stripe audio checkout creation failed: {e}')
        raise HTTPException(status_code=502, detail='Could not start checkout. Please try again.')
    await db.payment_transactions.insert_one({
        'session_id': session_id, 'user_id': user['id'], 'plan': AUDIO_UNLOCK_SKU,
        'audio_slug': body.slug, 'amount': AUDIO_UNLOCK_PRICE_USD, 'currency': 'usd',
        'provider': 'stripe', 'kind': 'one_time', 'auto_renew': False,
        'status': 'initiated', 'payment_status': 'pending', 'activated': False,
        'created_at': iso(now_utc()), 'updated_at': iso(now_utc()),
    })
    return {'ok': True, 'mock': False, 'checkout_url': session_url, 'session_id': session_id}


@router.get('/payments/status/{session_id}')
async def payment_status(session_id: str):
    record = await db.payment_transactions.find_one({'session_id': session_id})
    if not record:
        raise HTTPException(status_code=404, detail='Transaction not found')
    if record.get('payment_status') != 'paid':
        try:
            sdk = configure_stripe_sdk()
            s = sdk.checkout.Session.retrieve(session_id)
            if s.payment_status == 'paid' or s.status == 'complete':
                await db.payment_transactions.update_one(
                    {'session_id': session_id, 'payment_status': {'$ne': 'paid'}},
                    {'$set': {'status': 'completed', 'payment_status': 'paid',
                              'stripe_subscription_id': s.get('subscription'),
                              'updated_at': iso(now_utc())}},
                )
                record = await db.payment_transactions.find_one({'session_id': session_id})
            elif s.status == 'expired':
                await db.payment_transactions.update_one(
                    {'session_id': session_id},
                    {'$set': {'status': 'expired', 'payment_status': 'expired',
                              'updated_at': iso(now_utc())}},
                )
                record = await db.payment_transactions.find_one({'session_id': session_id})
        except Exception as e:
            logger.warning(f'Stripe status check failed for {session_id}: {e}')
    if record.get('payment_status') == 'paid':
        await activate_premium_from_transaction(record)
    return {'session_id': record['session_id'], 'status': record['status'],
            'payment_status': record['payment_status']}


@router.post('/webhook/stripe')
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get('Stripe-Signature')
    try:
        event = await stripe_client(str(request.base_url).rstrip('/') + '/api/webhook/stripe').handle_webhook(body, signature)
    except Exception as e:
        logger.warning(f'Stripe webhook rejected: {e}')
        raise HTTPException(status_code=400, detail='Invalid webhook')
    if event.session_id and event.payment_status == 'paid':
        await db.payment_transactions.update_one(
            {'session_id': event.session_id, 'payment_status': {'$ne': 'paid'}},
            {'$set': {'status': 'completed', 'payment_status': 'paid', 'updated_at': iso(now_utc())}},
        )
        record = await db.payment_transactions.find_one({'session_id': event.session_id})
        if record:
            await activate_premium_from_transaction(record)
    return {'status': 'ok'}


@router.post('/billing/cancel')
async def cancel_subscription(user=Depends(get_current_user)):
    sub = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if not sub:
        raise HTTPException(status_code=400, detail='No active subscription')
    # Cancel the recurring Razorpay Autopay mandate too
    if sub.get('auto_renew') and sub.get('razorpay_subscription_id') and RAZORPAY_ENABLED:
        try:
            await asyncio.to_thread(lambda: rzp.razorpay_client().subscription.cancel(sub['razorpay_subscription_id']))
        except Exception as e:
            logger.warning(f'Razorpay subscription cancel failed (continuing with local cancel): {e}')
    # Cancel the recurring subscription at Stripe too (own-key auto-renew mode)
    if sub.get('auto_renew') and sub.get('stripe_subscription_id') and not IS_SHARED_STRIPE_KEY:
        try:
            sdk = configure_stripe_sdk()
            sdk.Subscription.delete(sub['stripe_subscription_id'])
        except Exception as e:
            logger.warning(f'Stripe subscription cancel failed (continuing with local cancel): {e}')
    await db.subscriptions.update_one({'id': sub['id']}, {'$set': {'status': 'canceled', 'canceled_at': iso(now_utc())}})
    return {'ok': True, 'message': 'Subscription canceled. Premium access removed.'}


@router.get('/billing/subscription')
async def get_subscription(user=Depends(get_current_user)):
    sub = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    return {'subscription': clean(sub), 'is_premium': await is_entitled(user)}


@router.get('/billing/invoices')
async def get_invoices(user=Depends(get_current_user)):
    invoices = await db.invoices.find({'user_id': user['id']}).sort('created_at', -1).to_list(100)
    return {'invoices': [clean(i) for i in invoices]}
