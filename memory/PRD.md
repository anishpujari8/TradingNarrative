# PRD — The Trading Narrative

## Product
Subscription-based blog + newsletter ("Substack × premium magazine") covering 4 pillars:
Tech & Business, Finance, Lifestyle, Travel. FARM stack (FastAPI, React 19, MongoDB).

## Status: V1 COMPLETE (tested — backend 74/74, frontend 60/60 after fix)

## Implemented
- **Content**: 12 seeded editorial posts (3/category, mixed free/premium, 1 featured), author Jordan Hale.
- **Server-side paywall**: premium posts return only first 3 paragraphs via API to non-entitled users (cannot be bypassed via page source). Blur + fade + upgrade CTA in UI.
- **Auth**: email+password (bcrypt+JWT) AND magic link (email delivery MOCKED — link shown in UI dev-mode alert, single-use, 15-min expiry, rate-limited).
- **Billing (MOCKED, Stripe-ready)**: MOCK_BILLING=true; plans monthly $8 / annual $80; checkout dialog activates premium instantly, records invoice; cancel reverts instantly; billing history on /account. Env placeholders: STRIPE_SECRET_KEY, STRIPE_PRICE_MONTHLY, STRIPE_PRICE_ANNUAL.
- **Newsletter (MOCKED provider)**: capture forms (hero, home block, inline article, footer, about); subscribers in MongoDB; welcome + issue emails logged to email_logs; admin sends "issue from post" to all subscribers (mocked).
- **Pages**: Home (hero, featured, filterable grid, newsletter block), Article (reading layout, share rail, related, author bio), 4 Category pages, Archive (search + category/tier filters), Pricing (monthly/annual toggle, comparison table), About, Auth (3 tabs), Account (subscription manage/cancel + invoices), Admin Studio (Overview stats + recharts, Posts table CRUD, Editor with draft/publish/schedule + featured + tier, Newsletter subs/issues, Email log), 404.
- **Social sharing**: LinkedIn share-offsite URL, X intent, Instagram copy-link w/ toast, Web Share API, downloadable branded IG card (canvas, 1080×1080 + 1080×1920).
- **SEO**: /api/sitemap.xml (dynamic), robots.txt, OG/Twitter meta via react-helmet-async + index.html defaults.
- **Analytics**: pageview + CTA/checkout/share events stored in MongoDB, surfaced in admin Overview.
- **Design**: light editorial magazine (EB Garamond serif + Figtree), teal accent, dark mode toggle (persisted), grain overlay, framer-motion entrances, mobile-first.

## Credentials
- Admin: admin@tradingnarrative.com / Admin@2025 (see /app/memory/test_credentials.md)

## Mocked (swap-ready)
1. Stripe billing — real keys go in backend/.env; checkout endpoint has TODO branch for real Stripe.
2. Newsletter provider — adapter is `log_email()` in server.py; swap for Mailchimp/ConvertKit.
3. Magic-link + welcome emails — logged, not sent (needs Resend/SendGrid or provider).

## Future (Phase 3/4 per /app/plan.md)
- Password reset, scheduled-post preview, 7/30-day analytics trends, real Stripe + webhooks, real email provider.
