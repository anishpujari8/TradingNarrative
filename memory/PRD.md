# PRD — The Trading Narrative

## Product
Subscription-based blog + newsletter ("Substack × premium magazine") covering 4 pillars:
Tech & Business, Finance, Lifestyle, Travel. FARM stack (FastAPI, React 19, MongoDB).

## Status: V2.0 COMPLETE (iteration_4: backend 62/62; 2 frontend flags were false positives, verified working via UI)

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

## New in V2.0 (user's expanded spec applied to existing build)
- Pillars relabeled (same slugs/URLs): Tech & AI, Business & Finance, Personal Growth, Travel.
- Post TAGS: seeded, chips on articles → /archive?tag=X filter, admin editor input (comma-separated, max 10).
- INR pricing + Razorpay (MOCKED): currency auto-detect (Asia/Kolkata tz or -IN locale) + manual USD/INR toggle on pricing; ₹199/mo, ₹1,999/yr; mocked Razorpay dialog activates premium + INR invoice; REAL Razorpay path (order create, checkout.js, signature verify, webhook) dormant until RAZORPAY_KEY_ID/SECRET set in backend/.env.
- Email preferences in Account: newsletter on/off + per-pillar checkboxes (shown when subscribed); mocked issue sends filter recipients by category prefs.
- Comment reply NOTIFICATIONS: navbar bell + unread badge, mark-read on open, links to post.
- CONTINUE READING: progress saved per-article (localStorage ttn_progress), homepage strip with % bars, resume toast on revisit.
- WEEKLY DIGEST: admin preview (branded HTML email in iframe) + mocked send to subscribers.
- QUOTE CARD: third tab in IG share dialog with editable quote text (canvas, downloadable).
- About page follow-on-LinkedIn/Instagram buttons.

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

## V2.1 Session Update (Razorpay + Traffic + Lounge)
- **Razorpay INR checkout (LIVE, test mode)**: Real test keys configured. Account's Subscriptions/Autopay feature not yet enabled on Razorpay dashboard, so backend auto-falls back to one-time Orders (30/365-day passes). Startup probe flips to UPI Autopay mandates automatically once Subscriptions is enabled on the dashboard. Frontend handles both order and subscription checkout modes.
- **Traffic Sources Analytics**: First-pageview-per-session attribution via referrer + UTM params. Classifies LinkedIn, Instagram, X, Facebook, Google, YouTube, Reddit, WhatsApp, Telegram, Substack, etc. Admin → Traffic tab: stat cards, bar chart, source breakdown, top referring domains, UTM campaigns, 7/30/90-day selector. Endpoint: GET /api/admin/traffic.
- **Private Community Lounge (/lounge)**: Premium-members-only. Admin announcements (create/delete), member discussion threads with replies, delete own content, admin moderation, rate limits (5 threads/hr, 30 replies/hr). Locked states: signed-out → sign-in CTA; free user → upgrade CTA. Nav link "Lounge" added.
- Testing: iteration_5.json — backend 99.4%, frontend verified end-to-end.

## V2.2 Session Update (Autopay re-probe, Lounge notifications, Trends, Pins)
- **Autopay live switch-on**: Backend re-probes Razorpay Subscriptions capability (throttled, 10 min) on /billing/config and razorpay checkout — UPI Autopay activates automatically once enabled on the Razorpay dashboard, no restart needed.
- **Lounge notifications**: Replies to a member's Lounge discussion create a bell notification (type lounge_reply) for the thread author; clicking deep-links to /lounge?thread=<id> and auto-opens the discussion.
- **Traffic trends**: /api/admin/traffic now returns weekly 'trend' buckets + 'trend_series' (top 5 sources + Other); Admin Traffic tab shows a multi-line weekly chart.
- **Pinned discussions**: Admin-only POST /api/community/threads/{tid}/pin toggle; pinned threads sort first with a Pinned badge; pin toggle button in thread detail.
- Testing: iteration_6.json — backend 99.5% (183/184), frontend 100%, no regressions.

## V2.3 Session Update (Attribution, Autosend, Lock, CSV)
- **Post Attribution**: /api/admin/traffic returns 'landing_pages' (path × source × count); "Landing pages by source" table in Admin Traffic tab shows which content converts per channel.
- **Weekly Digest Autosend**: Background loop auto-sends the weekly digest every Friday (UTC), once per ISO week, when the admin toggle is on (currently ON). Toggle in Admin → Newsletter; endpoints GET/POST /api/admin/newsletter/autosend. Sends remain MOCKED (email_logs).
- **Lounge Thread Lock**: Admin-only POST /api/community/threads/{tid}/lock; locked threads stay readable but reject new replies (403); Locked badge + locked notice replace the reply composer.
- **CSV Export**: GET /api/admin/traffic/export?days=N streams a CSV (sources, referrers, campaigns, landing pages); one-click "Export CSV" button in the Traffic tab.
- Testing: iteration_7.json — backend 99.5% (208/209), frontend 100%, no regressions.

## V2.4 Session Update (Funnel, Gmail SMTP, Profiles, Scheduled Announcements)
- **Conversion Funnel**: Per-session tracking (sid) links arrival → pricing view → checkout click → premium activation, broken down per traffic source. GET /api/admin/funnel; funnel stage cards + per-source table in Admin Traffic tab. Demo funnel data seeded.
- **Real Email Sending (Gmail SMTP)**: Wired with user's Gmail (anishpujari8@gmail.com), From name "The Trading Narrative", Reply-To Hello@thetradingnarrative.com. IMPORTANT: user supplied a REGULAR Gmail password → SMTP auth fails (535); system gracefully falls back to logged sends. NEEDS a Gmail App Password (Google Account → Security → 2-Step Verification → App passwords) in GMAIL_SMTP_PASSWORD in backend/.env to go live. Admin → Email log tab has a status card + "Send test email" button; digest sends include full HTML.
- **Lounge Member Profiles**: GET /api/community/members/{uid} (premium-gated). Clicking any author in the Lounge opens a profile dialog: name, badges, member-since, discussion/reply counts, recent discussions (clickable).
- **Scheduled Announcements**: publish_at on announcements; future ones hidden from members, shown to admin with Scheduled badge + "publishes <date>"; datetime picker in the announcement dialog.
- Testing: iteration_8.json — backend 100% (261/262), frontend 100%, no regressions.

## V2.5 Session Update (Email LIVE, Pillar Digests, Announcement Editing, Plan Split)
- **REAL EMAIL SENDING IS LIVE**: Gmail App Password configured — /api/admin/email/status verified:true. Test email + a real pillar-personalized digest delivered to owner's Gmail. Welcome emails, issues, and digests all send for real now (with safe fallback to logging on failure).
- **Pillar Digests**: Weekly digest personalized per subscriber — only essays from their chosen pillars (Account → Email preferences checkboxes); subscribers with no matching posts are skipped. Digest HTML cached per pillar-combination.
- **Announcement Editing**: PUT /api/community/announcements/{aid}; pencil buttons on cards open the dialog in edit mode (prefilled incl. schedule); supports reschedule or clear-to-publish-now.
- **Funnel Plan Split**: conversions_monthly/conversions_annual per source + overall; Monthly/Annual columns in funnel table + split under 'Went Premium' card.
- Housekeeping: removed 12 fake test emails from newsletter_subscribers so live Gmail sending (incl. Friday autosend) doesn't hit invalid addresses. Owner's Gmail subscribed (tech pillar) as first real subscriber.
- Testing: iteration_9.json — backend 100%, frontend 100%, regression 100%.

## V2.6 Session Update (Unsubscribe, Growth Chart, Digest Preview, Post Conversions)
- **One-click Unsubscribe**: All marketing emails (digest/issue/welcome) carry an unsubscribe footer + List-Unsubscribe header. GET /api/newsletter/unsubscribe?email=&token= (stateless HMAC token) unsubscribes and shows a branded confirmation page; invalid token → 400.
- **Subscriber Growth Chart**: /api/admin/traffic returns subscriber_trend (weekly new + cumulative total); line chart in Admin → Traffic.
- **Digest Preview Email**: POST /api/admin/newsletter/send-digest-preview sends the full digest only to the owner's Gmail; "Send preview to me" button in the digest dialog (verified delivered for real).
- **Post Conversion Stats**: /api/admin/funnel returns post_conversions (per-essay reader sessions → premium conversions + rate); "Essays that convert" table in the funnel card.
- Stale "MOCKED" copy replaced with live-Gmail messaging in the digest dialog.
- Testing: latest iteration — backend 98.2% (one wrong test expectation, implementation correct), frontend 100%, all regressions pass, email-safety compliant.
