# PRD — The Trading Narrative

## Product
Subscription-based blog + newsletter ("Substack × premium magazine") covering 4 pillars:
Tech & Business, Finance, Lifestyle, Travel. FARM stack (FastAPI, React 19, MongoDB).

## Status: V1.2 COMPLETE (iteration_3: backend 120/120, frontend 43/43)

## Implemented
- **Content**: 12 seeded editorial posts (3/category, mixed free/premium, 1 featured), author Jordan Hale.
- **Server-side paywall**: premium posts return only first 3 paragraphs via API to non-entitled users (cannot be bypassed via page source). Blur + fade + upgrade CTA in UI.
- **Auth**: email+password (bcrypt+JWT) AND magic link (email delivery MOCKED — link shown in UI dev-mode alert, single-use, 15-min expiry, rate-limited).
- **Billing (REAL Stripe, TEST MODE)**: MOCK_BILLING=false; emergentintegrations StripeCheckout with STRIPE_API_KEY (currently shared test key sk_test_emergent — user's own key can replace it in backend/.env). Hosted Stripe Checkout: monthly $8 → 30 days premium, annual $80 → 365 days (one-time payments granting timed access; note: claimable-sandbox recurring subscriptions unavailable — account country IN not supported by Stripe sandboxes). Payment flow: /api/billing/checkout → checkout.stripe.com → /payment/success polls /api/payments/status/{id} → server-side activation (idempotent) + invoice; webhook at /api/webhook/stripe; /payment/cancel page; cancel from /account reverts instantly. Test card 4242 4242 4242 4242.
- **Newsletter (MOCKED provider)**: capture forms (hero, home block, inline article, footer, about); subscribers in MongoDB; welcome + issue emails logged to email_logs; admin sends "issue from post" to all subscribers (mocked).
- **Pages**: Home (hero, featured, filterable grid, newsletter block), Article (reading layout, share rail, related, author bio), 4 Category pages, Archive (search + category/tier filters), Pricing (monthly/annual toggle, comparison table), About, Auth (3 tabs), Account (subscription manage/cancel + invoices), Admin Studio (Overview stats + recharts, Posts table CRUD, Editor with draft/publish/schedule + featured + tier, Newsletter subs/issues, Email log), 404.
- **Social sharing**: LinkedIn share-offsite URL, X intent, Instagram copy-link w/ toast, Web Share API, downloadable branded IG card (canvas, 1080×1080 + 1080×1920).
- **SEO**: /api/sitemap.xml (dynamic), robots.txt, OG/Twitter meta via react-helmet-async + index.html defaults.
- **Analytics**: pageview + CTA/checkout/share events stored in MongoDB, surfaced in admin Overview.
- **Design**: light editorial magazine (EB Garamond serif + Figtree), teal accent, dark mode toggle (persisted), grain overlay, framer-motion entrances, mobile-first.

## Credentials
- Admin: admin@tradingnarrative.com / Admin@2025 (see /app/memory/test_credentials.md)

## New in V1.2
- Reply threads on comments (1-level nesting, flattened deeper replies, cascade delete), bookmarks/reading list (/reading-list, article Save button + card overlay icon, any logged-in user), 'For you' homepage recommendations (localStorage ttn_read_history + server pageview history, weighted by category via GET /api/recommendations), auto-renew-ready billing: billing/config exposes auto_renew; with shared sk_test_emergent key → one-time passes (proxy blocks Subscription cancel API); paste user's own key into STRIPE_API_KEY → subscription-mode checkout (recurring price_data), Stripe-side cancel, real period end. Branch dormant until key provided.

## New in V1.1
- Real Stripe test-mode checkout (above), password reset flow (mocked email — link shown in UI, single-use, 15-min expiry, rate-limited), premium-member comments on articles (read: everyone; post: premium/admin; delete: owner/admin), reading progress bar + "min left" pill on articles.

## Mocked (swap-ready)
1. Emails (password reset, magic link, welcome, newsletter issues) — logged to email_logs, links surfaced in UI dev-mode alerts.
2. Newsletter provider — adapter is `log_email()` in server.py; swap for Mailchimp/ConvertKit.
3. Stripe uses shared TEST key — user can paste their own sk_test key into STRIPE_API_KEY in backend/.env (restart backend).

## Future
- Recurring auto-renew subscriptions + Stripe customer portal (needs user's own Stripe account with subscriptions), real email provider, 7/30-day analytics trends, scheduled-post preview.
