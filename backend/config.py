"""Central configuration: env loading, constants, logger."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ttn')

JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret')
JWT_ALGO = 'HS256'
JWT_EXPIRY_DAYS = 30
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
MOCK_BILLING = os.environ.get('MOCK_BILLING', 'true').lower() == 'true'
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')
# Shared Emergent test key: one-time timed passes (proxy blocks Subscription cancel API).
# User's own key: true auto-renewing subscriptions + Stripe-side cancellation.
IS_SHARED_STRIPE_KEY = 'sk_test_emergent' in STRIPE_API_KEY
AUTO_RENEW = not IS_SHARED_STRIPE_KEY

RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

PLANS = {
    'monthly': {'id': 'monthly', 'label': 'Monthly', 'amount': 1.04, 'currency': 'usd',
                'amount_inr': 99.00, 'interval': 'month', 'period_days': 30},
    'annual': {'id': 'annual', 'label': 'Annual', 'amount': 10.50, 'currency': 'usd',
               'amount_inr': 999.00, 'interval': 'year', 'period_days': 365},
    'founding_monthly': {'id': 'founding_monthly', 'label': 'Founding Member Monthly', 'amount': 4.80,
                         'currency': 'usd', 'amount_inr': 458.00, 'interval': 'month', 'period_days': 30},
    'founding': {'id': 'founding', 'label': 'Founding Member', 'amount': 57.69, 'currency': 'usd',
                 'amount_inr': 5499.00, 'interval': 'year', 'period_days': 365},
}

# Early bird launch offer: the first EARLY_BIRD_SPOTS premium subscribers get a
# discounted FIRST period (monthly: first month, annual: first year), then regular price.
EARLY_BIRD_SPOTS = 50
EARLY_BIRD_PRICES = {
    'monthly': {'amount': 0.52, 'amount_inr': 49.00},
    'annual': {'amount': 5.25, 'amount_inr': 499.00},
}

# Per-essay audio narration unlock: one-time micro-purchase for free readers.
# NARRATION POLICY: newsletter editions + shipping industry essays keep free full audio;
# every other essay narration can be unlocked a la carte at this price.
AUDIO_UNLOCK_SKU = 'audio_unlock'
AUDIO_UNLOCK_PRICE_USD = 0.50  # Stripe hard minimum is $0.50 per charge
AUDIO_UNLOCK_PRICE_INR = 45.00

CATEGORIES = {
    'tech-business': 'Tech & AI',
    'finance': 'Business & Finance',
    'lifestyle': 'Personal Growth',
    'delivery': 'Delivery & Systems',
}

PREVIEW_BLOCKS = 3  # paragraphs shown to non-premium users on premium posts

GMAIL_SMTP_USER = os.environ.get('GMAIL_SMTP_USER', '')
GMAIL_SMTP_PASSWORD = os.environ.get('GMAIL_SMTP_PASSWORD', '')
EMAIL_FROM_NAME = os.environ.get('EMAIL_FROM_NAME', 'The Trading Narrative')
EMAIL_REPLY_TO = os.environ.get('EMAIL_REPLY_TO', '')
EMAIL_ENABLED = bool(GMAIL_SMTP_USER and GMAIL_SMTP_PASSWORD)

MARKETING_KINDS = {'digest', 'issue', 'welcome'}

# Admin notifications: alerted whenever someone subscribes (newsletter or paid)
ADMIN_NOTIFY_EMAIL = os.environ.get('ADMIN_NOTIFY_EMAIL', 'anishpujari8@gmail.com')

# Launch promo: the first N registered readers can read the first 5 published essays free
EARLY_SUPPORTER_LIMIT = 50
EARLY_FREE_POSTS = 5

# Metered anonymous access (SEO-friendly freemium): logged-out visitors may read
# METER_FREE_READS complete free-tier essays before hitting the paywall preview.
METER_FREE_READS = 3
METER_COOKIE = 'fv_slugs'
METER_COOKIE_DAYS = 90
PREVIEW_WORDS = 250  # locked-essay preview budget (or first 2 blocks, whichever is shorter)

# ElevenLabs narration (Essay Audio)
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
TTS_ENABLED = bool(ELEVENLABS_API_KEY)
TTS_MODEL = 'eleven_turbo_v2_5'  # half the credit cost of multilingual_v2, near-identical narration quality
TTS_OUTPUT_FORMAT = 'mp3_44100_64'  # spoken word: good quality, ~0.5 MB/min
AUDIO_CLIP_SECONDS = 20  # free members hear this much of every narration
AUDIO_CLIP_BYTES = AUDIO_CLIP_SECONDS * 8000  # 64 kbps mp3 ≈ 8 KB per second
TTS_VOICES = {
    'male': {'id': 'JBFqnCBsd6RMkjVDRZzb', 'label': 'George — warm male'},
    'female': {'id': '21m00Tcm4TlvDq8ikWAM', 'label': 'Rachel — warm female'},
    'documentary': {'id': 'onwK4e9ZLuTAKqWW03F9', 'label': 'Daniel — documentary'},
}

# Production deployment of this app (used by the admin Content Sync tool)
PRODUCTION_SITE_URL = os.environ.get('PRODUCTION_SITE_URL', 'https://thetradingnarrative.com').rstrip('/')

# AI features (Gemini via the Emergent universal LLM key)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
AI_ENABLED = bool(EMERGENT_LLM_KEY)
AI_PROVIDER = 'gemini'
AI_MODEL = 'gemini-2.5-flash'

# Editorial series: curated, ordered collections of essays
SERIES = {
    'trading-operations': {
        'slug': 'trading-operations',
        'title': 'Trading Operations',
        'description': ('A running series on the operational backbone of commodity trading — '
                        'freight, demurrage, market structure, and the data discipline that '
                        'separates good desks from great ones.'),
        'post_slugs': [
            'five-things-commodity-desks-need-to-know-this-week',
            'freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr',
            'the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a',
        ],
    },
}
