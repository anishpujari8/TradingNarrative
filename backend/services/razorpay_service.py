"""Razorpay client + Subscriptions (UPI Autopay) capability probing.

Mutable module state: RAZORPAY_SUBS_ENABLED, RAZORPAY_LAST_PROBE — always read via
module attribute (e.g. `rzp.RAZORPAY_SUBS_ENABLED`) so callers see live updates.
"""
import asyncio

from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_ENABLED, PLANS, logger
from db import db

RAZORPAY_SUBS_ENABLED = False  # probed at startup — True when the account has Subscriptions (UPI Autopay) enabled
RAZORPAY_LAST_PROBE = 0.0  # unix ts of last capability probe (throttles live re-checks)


def razorpay_client():
    import razorpay
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


async def probe_razorpay_subscriptions():
    global RAZORPAY_SUBS_ENABLED
    if not RAZORPAY_ENABLED:
        RAZORPAY_SUBS_ENABLED = False
        return
    try:
        await asyncio.to_thread(lambda: razorpay_client().subscription.all({'count': 1}))
        RAZORPAY_SUBS_ENABLED = True
        logger.info('Razorpay Subscriptions (UPI Autopay) ENABLED on this account')
    except Exception:
        RAZORPAY_SUBS_ENABLED = False
        logger.info('Razorpay Subscriptions not enabled on this account — using one-time INR passes')


async def maybe_reprobe_razorpay(force: bool = False):
    """Live re-check of the Subscriptions capability (max once per 10 min) so
    UPI Autopay switches on automatically once enabled on the Razorpay dashboard,
    without needing a backend restart."""
    global RAZORPAY_LAST_PROBE
    import time as _time
    if not RAZORPAY_ENABLED or RAZORPAY_SUBS_ENABLED:
        return
    if not force and _time.time() - RAZORPAY_LAST_PROBE < 600:
        return
    RAZORPAY_LAST_PROBE = _time.time()
    await probe_razorpay_subscriptions()


async def get_or_create_razorpay_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    # amount is part of the cache key: a price change automatically mints a fresh Razorpay plan
    key = f'razorpay_plan_{plan_id}_{int(plan["amount_inr"])}'
    stored = await db.config.find_one({'key': key})
    if stored:
        return stored['value']
    rz_plan = await asyncio.to_thread(lambda: razorpay_client().plan.create({
        'period': 'monthly' if plan_id == 'monthly' else 'yearly', 'interval': 1,
        'item': {'name': f"The Trading Narrative Premium — {plan['label']} (INR)",
                 'amount': int(round(plan['amount_inr'] * 100)), 'currency': 'INR'},
    }))
    await db.config.update_one({'key': key}, {'$set': {'value': rz_plan['id']}}, upsert=True)
    return rz_plan['id']
