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
    'monthly': {'id': 'monthly', 'label': 'Monthly', 'amount': 10.00, 'currency': 'usd',
                'amount_inr': 399.00, 'interval': 'month', 'period_days': 30},
    'annual': {'id': 'annual', 'label': 'Annual', 'amount': 100.00, 'currency': 'usd',
               'amount_inr': 3999.00, 'interval': 'year', 'period_days': 365},
    'founding': {'id': 'founding', 'label': 'Founding Member', 'amount': 250.00, 'currency': 'usd',
                 'amount_inr': 9999.00, 'interval': 'year', 'period_days': 365},
}

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

# ElevenLabs narration (Essay Audio)
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
TTS_ENABLED = bool(ELEVENLABS_API_KEY)
TTS_MODEL = 'eleven_turbo_v2_5'  # half the credit cost of multilingual_v2, near-identical narration quality
TTS_OUTPUT_FORMAT = 'mp3_44100_64'  # spoken word: good quality, ~0.5 MB/min
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
