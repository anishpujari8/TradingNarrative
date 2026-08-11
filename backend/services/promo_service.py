"""Early bird premium launch offer: first N premium subscribers get a discounted first period."""
from config import EARLY_BIRD_SPOTS, EARLY_BIRD_PRICES, PLANS
from db import db


async def early_bird_status():
    """Public promo state: spots claimed by activated early-bird subscriptions."""
    claimed = await db.subscriptions.count_documents({'early_bird': True})
    remaining = max(0, EARLY_BIRD_SPOTS - claimed)
    return {
        'active': remaining > 0,
        'spots': EARLY_BIRD_SPOTS,
        'claimed': claimed,
        'remaining': remaining,
        'plans': {
            pid: {
                'amount': p['amount'], 'amount_inr': p['amount_inr'],
                'regular_amount': PLANS[pid]['amount'],
                'regular_amount_inr': PLANS[pid]['amount_inr'],
                'interval': PLANS[pid]['interval'],
            }
            for pid, p in EARLY_BIRD_PRICES.items()
        },
    }


async def early_bird_price(plan_id: str):
    """Resolve checkout pricing: (is_early_bird, usd_amount, inr_amount).
    Falls back to regular plan pricing when the promo is over or plan not covered."""
    plan = PLANS[plan_id]
    if plan_id not in EARLY_BIRD_PRICES:
        return False, plan['amount'], plan['amount_inr']
    status = await early_bird_status()
    if not status['active']:
        return False, plan['amount'], plan['amount_inr']
    eb = EARLY_BIRD_PRICES[plan_id]
    return True, eb['amount'], eb['amount_inr']
