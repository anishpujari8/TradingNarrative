"""Razorpay (INR / UPI) routes: checkout, verify, webhook."""
import os
import uuid
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Request

from config import (RAZORPAY_ENABLED, RAZORPAY_KEY_ID, PLANS, AUDIO_UNLOCK_SKU,
                    AUDIO_UNLOCK_PRICE_INR, logger)
from db import db
from utils import now_utc, iso, published_query, has_free_audio, owns_audio, premium_audio_only
from security import get_current_user, is_entitled
from schemas import RazorpayCheckoutIn, RazorpayVerifyIn, AudioCheckoutIn
from services import razorpay_service as rzp
from services.stripe_service import activate_premium_from_transaction

router = APIRouter(prefix='/api')


@router.post('/billing/razorpay/checkout')
async def razorpay_checkout(body: RazorpayCheckoutIn, user=Depends(get_current_user)):
    if body.plan not in PLANS:
        raise HTTPException(status_code=400, detail='Invalid plan')
    existing = await db.subscriptions.find_one({'user_id': user['id'], 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail='You already have an active subscription')
    plan = PLANS[body.plan]
    amount_paise = int(round(plan['amount_inr'] * 100))
    await rzp.maybe_reprobe_razorpay()  # switch to Autopay live once enabled on the dashboard
    kind = 'order'
    mock = False
    if RAZORPAY_ENABLED and rzp.RAZORPAY_SUBS_ENABLED:
        # UPI AUTOPAY: recurring subscription via e-mandate
        try:
            rz_plan_id = await rzp.get_or_create_razorpay_plan(body.plan)
            sub = await asyncio.to_thread(lambda: rzp.razorpay_client().subscription.create({
                'plan_id': rz_plan_id,
                'total_count': 120 if PLANS[body.plan]['interval'] == 'month' else 10,
                'customer_notify': 1,
                'notes': {'user_id': user['id'], 'plan': body.plan},
            }))
            ref_id = sub['id']
            kind = 'subscription'
        except Exception as e:
            logger.error(f'Razorpay subscription creation failed: {e}')
            raise HTTPException(status_code=502, detail='Could not start Razorpay Autopay checkout.')
    elif RAZORPAY_ENABLED:
        # One-time order (Autopay switches on automatically once Subscriptions is enabled on the account)
        try:
            order = await asyncio.to_thread(lambda: rzp.razorpay_client().order.create({
                'amount': amount_paise, 'currency': 'INR', 'payment_capture': 1,
                'receipt': f'ttn-{user["id"][:12]}-{body.plan}'[:40],
                'notes': {'user_id': user['id'], 'plan': body.plan},
            }))
        except Exception as e:
            logger.error(f'Razorpay order creation failed: {e}')
            raise HTTPException(status_code=502, detail='Could not start Razorpay checkout.')
        ref_id = order['id']
    else:
        # MOCKED order — structure mirrors the real integration 1:1
        ref_id = f'order_mock_{uuid.uuid4().hex[:14]}'
        mock = True
    await db.payment_transactions.insert_one({
        'session_id': ref_id, 'user_id': user['id'], 'plan': body.plan,
        'amount': plan['amount_inr'], 'currency': 'inr', 'provider': 'razorpay',
        'kind': kind, 'auto_renew': kind == 'subscription', 'mock': mock,
        'status': 'initiated', 'payment_status': 'pending', 'activated': False,
        'created_at': iso(now_utc()), 'updated_at': iso(now_utc()),
    })
    return {'ok': True, 'mock': mock, 'kind': kind,
            'order_id': ref_id if kind == 'order' else None,
            'subscription_id': ref_id if kind == 'subscription' else None,
            'ref_id': ref_id,
            'amount': amount_paise, 'currency': 'INR',
            'razorpay_key_id': RAZORPAY_KEY_ID or None,
            'name': 'The Trading Narrative',
            'description': f"Premium — {plan['label']} (INR)"}


@router.post('/billing/audio/razorpay/checkout')
async def razorpay_audio_checkout(body: AudioCheckoutIn, user=Depends(get_current_user)):
    """One-time Razorpay order (₹45) unlocking a single essay's full narration."""
    post = await db.posts.find_one({'slug': body.slug, **published_query()})
    if not post:
        raise HTTPException(status_code=404, detail='Essay not found')
    if await is_entitled(user):
        raise HTTPException(status_code=400, detail='Premium members already enjoy full narrations')
    if premium_audio_only(post):
        raise HTTPException(status_code=400, detail='This narration is exclusive to Premium members')
    if has_free_audio(post):
        raise HTTPException(status_code=400, detail='This narration is already free to listen')
    if owns_audio(user, body.slug):
        raise HTTPException(status_code=400, detail='You already own this narration')
    amount_paise = int(round(AUDIO_UNLOCK_PRICE_INR * 100))
    mock = False
    if RAZORPAY_ENABLED:
        try:
            order = await asyncio.to_thread(lambda: rzp.razorpay_client().order.create({
                'amount': amount_paise, 'currency': 'INR', 'payment_capture': 1,
                'receipt': f'ttn-au-{user["id"][:12]}'[:40],
                'notes': {'user_id': user['id'], 'sku': AUDIO_UNLOCK_SKU, 'slug': body.slug},
            }))
        except Exception as e:
            logger.error(f'Razorpay audio order creation failed: {e}')
            raise HTTPException(status_code=502, detail='Could not start Razorpay checkout.')
        ref_id = order['id']
    else:
        # MOCKED order — structure mirrors the real integration 1:1
        ref_id = f'order_mock_{uuid.uuid4().hex[:14]}'
        mock = True
    await db.payment_transactions.insert_one({
        'session_id': ref_id, 'user_id': user['id'], 'plan': AUDIO_UNLOCK_SKU,
        'audio_slug': body.slug, 'amount': AUDIO_UNLOCK_PRICE_INR, 'currency': 'inr',
        'provider': 'razorpay', 'kind': 'order', 'auto_renew': False, 'mock': mock,
        'status': 'initiated', 'payment_status': 'pending', 'activated': False,
        'created_at': iso(now_utc()), 'updated_at': iso(now_utc()),
    })
    return {'ok': True, 'mock': mock, 'kind': 'order',
            'order_id': ref_id, 'ref_id': ref_id,
            'amount': amount_paise, 'currency': 'INR',
            'razorpay_key_id': RAZORPAY_KEY_ID or None,
            'name': 'The Trading Narrative',
            'description': f"Audio narration — {post['title'][:60]}"}


@router.post('/billing/razorpay/verify')
async def razorpay_verify(body: RazorpayVerifyIn, user=Depends(get_current_user)):
    txn = await db.payment_transactions.find_one({'session_id': body.order_id, 'user_id': user['id']})
    if not txn:
        raise HTTPException(status_code=404, detail='Order not found')
    if txn.get('payment_status') == 'paid':
        return {'ok': True, 'already': True}
    if txn.get('mock'):
        # MOCKED: mark paid instantly (no gateway available without keys)
        pass
    elif txn.get('kind') == 'subscription':
        try:
            rzp.razorpay_client().utility.verify_subscription_payment_signature({
                'razorpay_subscription_id': body.order_id,
                'razorpay_payment_id': body.payment_id,
                'razorpay_signature': body.signature,
            })
        except Exception:
            raise HTTPException(status_code=400, detail='Payment signature verification failed')
    else:
        try:
            rzp.razorpay_client().utility.verify_payment_signature({
                'razorpay_order_id': body.order_id,
                'razorpay_payment_id': body.payment_id,
                'razorpay_signature': body.signature,
            })
        except Exception:
            raise HTTPException(status_code=400, detail='Payment signature verification failed')
    await db.payment_transactions.update_one(
        {'session_id': body.order_id, 'payment_status': {'$ne': 'paid'}},
        {'$set': {'status': 'completed', 'payment_status': 'paid',
                  'razorpay_payment_id': body.payment_id, 'updated_at': iso(now_utc())}},
    )
    txn = await db.payment_transactions.find_one({'session_id': body.order_id})
    await activate_premium_from_transaction(txn)
    return {'ok': True, 'mock': bool(txn.get('mock'))}


@router.post('/webhook/razorpay')
async def razorpay_webhook(request: Request):
    if not RAZORPAY_ENABLED:
        return {'status': 'ignored (razorpay not configured)'}
    payload = await request.body()
    signature = request.headers.get('X-Razorpay-Signature', '')
    secret = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    try:
        rzp.razorpay_client().utility.verify_webhook_signature(payload.decode(), signature, secret)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid webhook signature')
    import json as _json
    event = _json.loads(payload)
    if event.get('event') == 'payment.captured':
        order_id = event['payload']['payment']['entity'].get('order_id')
        if order_id:
            await db.payment_transactions.update_one(
                {'session_id': order_id, 'payment_status': {'$ne': 'paid'}},
                {'$set': {'status': 'completed', 'payment_status': 'paid', 'updated_at': iso(now_utc())}},
            )
            txn = await db.payment_transactions.find_one({'session_id': order_id})
            if txn:
                await activate_premium_from_transaction(txn)
    return {'status': 'ok'}
