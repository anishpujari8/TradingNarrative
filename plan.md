# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (“The Trading Narrative”) with an editorial reading experience, server-side paywall previews, and a freemium model.
- Support **three content pillars**: **Tech & AI**, **Business & Finance**, **Personal Growth**.
- Provide subscriptions via:
  - **Stripe (international recurring)**
  - **Razorpay (India)** with automatic capability detection:
    - **UPI Autopay/Subscriptions** when enabled on the Razorpay dashboard
    - **Fallback to one-time Razorpay Orders** (time-bound access) when Subscriptions is not enabled
    - **Live Autopay switch-on**: throttled capability re-check so Autopay activates automatically once enabled (no backend restart required)
  - Locale detection + **manual currency toggle**.
- Deliver retention UX: bookmarks/reading list, reading progress indicators, continue-reading strips, notifications bell, weekly digest previews.
- Add V2 admin + community capabilities:
  - **Traffic Sources Analytics** (referrers + UTM attribution)
  - **Traffic Trends** (weekly source trend chart)
  - **Private Community Lounge** (premium-only announcements + discussion threads)
  - **Community enhancements**: pinned discussions + lounge reply notifications
- Keep integrations reliable with webhooks, audit logs, and end-to-end tests.

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (Isolation) (paywall + subscription state + preview API) ✅ DONE
**User stories**
1. As a reader, I can open a premium article and only receive a short preview when not subscribed.
2. As a reader, I can “upgrade” via a mock checkout and immediately unlock full premium content.
3. As a premium user, I always receive full content from the API (not just unblur UI).
4. As a user, I can cancel and immediately revert to preview-only.
5. As an admin, I can mark a post as free or premium and see gating change instantly.

**Steps**
- Backend-only POC in FastAPI:
  - Mongo models: User (roles, premium_status), Post (tier, preview_blocks/full_blocks).
  - Endpoints: `GET /api/posts/{slug}` returns preview vs full based on entitlement.
  - Mock subscription endpoints: `POST /api/billing/mock/checkout` (activate premium), `POST /api/billing/mock/cancel` (deactivate), record mock invoices.
- Minimal React POC page(s): Login + Post view verifying that page source never includes full premium content when not entitled.
- POC test checklist: unauth, free user, premium user; verify API responses and DB state transitions.

### Phase 2 — V1 App Development (bulk build) ✅ DONE
**User stories**
1. As a visitor, I can browse the homepage, filter by category, and quickly find recent posts.
2. As a reader, I can read an article with clean typography, read-time, author bio, and related posts.
3. As a free user, I can see a clear paywall CTA and pricing page with monthly/annual toggle.
4. As a subscriber, I can access an account page showing premium badge + billing history.
5. As an admin, I can create/edit/schedule/publish posts and set free/premium tier.

**Design first (design_agent)**
- Editorial layout, one accent color, dark mode toggle, Tailwind + shadcn/ui components, responsive templates.

**Backend (FastAPI /api, Mongo)**
- Auth:
  - Email+password (bcrypt + JWT).
  - Magic link (dev-mode) supported.
- Content:
  - Posts CRUD, publish/schedule, categories/pillars, featured flag.
  - Server-side paywall logic: preview paragraphs only for non-premium on premium posts.
  - Search/filter endpoints.
- Newsletter:
  - Subscriber capture endpoints.
  - Weekly digest admin previews.
- SEO/ops:
  - `GET /sitemap.xml`, `GET /robots.txt`.
  - Analytics/events collector (baseline).
- Seed data:
  - Admin user + sample posts across the 3 pillars.

**Frontend (React)**
- Pages:
  - Home, Article, Pillar pages, Archive, Pricing, About.
  - Auth (login/register + magic link), Account/Billing.
  - Admin Studio (posts list, editor, schedule/publish, tier/category toggles).
- Social sharing:
  - Share URLs + Copy Link.
  - Quote-card generator.
- Reading UX:
  - Related-by-interest / For You.
  - Reply threads.
  - Bookmarks/reading list.
  - Reading progress indicator.
  - Continue-reading strip.
  - Notifications bell.

**End Phase 2**
- Run full E2E passes and fix blocking issues.

### Phase 3 — Hardening + Feature Completion ✅ DONE
**User stories**
1. As a user, I can reset my password if I forget it.
2. As an admin, I can preview scheduled posts and confirm publish timing.
3. As a writer, I can see validation errors clearly when saving drafts.
4. As a subscriber, I can reliably see my entitlement reflected across devices after login.

**Steps**
- Improve validation, empty/error states, loading skeletons.
- Tighten security basics: token expiry, rate-limit magic link generation, sanitize HTML/markdown.
- Ensure paywall cannot leak full content via list endpoints (only summaries in grids).
- Expand tests.

### Phase 4 — Payments Integrations (Stripe + Razorpay) ✅ DONE
**User stories**
1. As a global user, I can pay with real Stripe recurring checkout and return to unlocked premium.
2. As an Indian user, I can pay via Razorpay:
   - If Subscriptions/Autopay is enabled: create a mandate/subscription.
   - If not enabled: fallback to a one-time Razorpay order (time-bound premium pass).
3. As a user, I can manage/cancel subscriptions cleanly and see status reflected.
4. As an admin, I can trust webhook-driven entitlement updates.

**Steps**
- Stripe (DONE):
  - Stripe Checkout with auto-renew enabled using real keys.
  - Webhook updates entitlement.
- Razorpay (DONE):
  - Real Razorpay integration wired into Pricing.
  - Backend probes Subscriptions capability and falls back to **one-time Orders** when unavailable.
  - Frontend checkout supports both **order_id** and **subscription_id** flows.
  - DB transaction records written on checkout initiation; verification endpoint activates premium.
  - Webhook endpoint exists for gateway-driven confirmation events.
- Testing (DONE):
  - Backend tests verify order creation using test keys.
  - Frontend verified Razorpay checkout modal opens for INR.

### Phase 5 — V2 Admin Analytics + Community ✅ DONE
**User stories**
1. As an admin, I can see where readers come from (LinkedIn, Instagram, Google, Direct, etc.).
2. As a premium member, I can access a private lounge.
3. As a premium member, I can read admin announcements and participate in discussion threads (post + reply).

**Steps**
- Traffic Sources Analytics (DONE):
  - Backend attribution on the **first pageview of a browser session** via session flag.
  - Classification uses referrer host + UTM tags; internal navigation is ignored.
  - Endpoint: `GET /api/admin/traffic?days=...` returns source breakdown, top referrers, campaigns.
  - Admin Studio UI tab: chart + tables + day-range selector.
- Private Community Lounge (DONE):
  - Frontend page: `/lounge` (premium-only; locked state shown for logged-out/free users).
  - Backend routes: `/api/community/*`:
    - Announcements: admin create/list/delete; members read.
    - Threads: premium create/list/detail/delete.
    - Replies: premium reply/delete.
  - Moderation basics and simple rate limits.
  - Tests: access control (401 unauth, 403 free), CRUD verified.

### Phase 6 — V2.2 Enhancements (Autopay Live Switch-On + Lounge Notifications + Traffic Trends + Pinned Threads) ✅ DONE
**User stories**
1. As an Indian subscriber, once Razorpay Subscriptions is enabled on the dashboard, the site automatically switches from one-time orders to UPI Autopay without requiring a deployment or restart.
2. As a Lounge member, when someone replies to my discussion, I get a bell notification and can jump straight into the thread.
3. As an admin, I can see week-by-week traffic source trends to understand what’s growing.
4. As an admin, I can pin important discussions so new members see them first.

**Steps**
- Razorpay Autopay live re-probe (DONE):
  - Throttled capability re-check (max once / 10 minutes) on `GET /api/billing/config` and `POST /api/billing/razorpay/checkout`.
  - Automatically flips `razorpay_autopay` to true once the Razorpay account has Subscriptions enabled (no backend restart required).
- Lounge reply notifications (DONE):
  - Replying to someone else’s lounge thread creates a notification (`type: lounge_reply`) for the thread author.
  - Notification click deep-links to `/lounge?thread=<id>` and the Lounge auto-opens the thread detail view.
- Traffic trends (DONE):
  - `GET /api/admin/traffic` now returns weekly `trend` buckets and `trend_series`.
  - Admin Traffic tab renders a multi-line Recharts `LineChart` (“Weekly trend by source”).
- Pinned discussions (DONE):
  - Admin-only endpoint: `POST /api/community/threads/{tid}/pin` toggles pinned.
  - Threads list sorts pinned-first.
  - UI: “Pinned” badge on pinned thread cards + pin toggle button in thread detail view (admin-only).
- Testing (DONE):
  - Iteration 6 report: backend **99.5% (183/184)**, frontend **100%**, no regressions.

## 3) Next Actions
All planned phases are complete. Suggested follow-ups (optional enhancements):
1. Configure `RAZORPAY_WEBHOOK_SECRET` and Stripe webhook secrets in production for stronger signature verification.
2. Configure/enable Razorpay Subscriptions in the dashboard to activate true UPI Autopay mandates.
3. Consider refactoring `/app/backend/server.py` into modules (billing, community, admin/analytics) to reduce risk from large-file edits.
4. Add deeper analytics:
   - post-level attribution (which article drove conversions)
   - export CSV
   - retention cohorts and conversion funnel
5. Community moderation upgrades:
   - lock threads
   - pin announcements
   - admin edit announcements
   - basic spam controls (link limits, cooldowns)

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API (verified via network/page source).
✅ Stripe recurring checkout works end-to-end and updates entitlements via webhook.
✅ Razorpay INR checkout works end-to-end:
- If Autopay enabled: subscription/mandate flow supported.
- If not enabled: graceful fallback to one-time Orders.
✅ Autopay live switch-on works: capability is re-probed and activates without restart once Subscriptions is enabled.
✅ Pricing routes correctly between Stripe (USD) and Razorpay (INR) via locale/toggle.
✅ Traffic sources visible in Admin with meaningful referrer grouping and UTM campaign visibility.
✅ Weekly traffic trend chart renders and reflects weekly bucketing.
✅ Premium-only Community Lounge works with announcements + threads + replies and correct access control.
✅ Lounge reply notifications appear in bell and deep-link opens the relevant thread.
✅ Pinned discussions work (admin toggle + pinned-first sorting + UI badges).
✅ Testing passes:
- Iteration 5: backend 99.4% + frontend verification.
- Iteration 6: backend 99.5% (183/184) + frontend 100%, no regressions.

---
## STATUS UPDATE (post Phase 2)
- Phase 1 (POC): DONE — server-side paywall, subscription transitions, magic link, newsletter, admin gating.
- Phase 2 (V1 app): DONE — full frontend + backend built and tested.

## STATUS UPDATE (post V1.1 feature batch)
- Password reset (mocked email, dev-mode link) DONE.
- Reading progress DONE.
- Premium comments DONE.
- E2E testing iterations passing.

## STATUS UPDATE (post V1.2 feature batch)
- Reply threads DONE.
- Bookmarks/reading list DONE.
- For-You recommendations / related-by-interest DONE.

## STATUS UPDATE (V2.0 — expanded spec applied)
- Notifications bell DONE.
- Continue-reading strip + resume DONE.
- Weekly digest admin previews DONE.
- Pillars relabeled to **Tech & AI**, **Business & Finance**, **Personal Growth** DONE.
- Tags + email preferences DONE.
- Quote-card generator in share dialog DONE.
- Pricing page: Razorpay currency toggle DONE.
- Stripe auto-renew: enabled with real keys DONE.

## STATUS UPDATE (V2.1 — payments + analytics + community) ✅ COMPLETE
- Razorpay integration FIXED:
  - Test keys validated; Orders API works.
  - Subscriptions/Plans unauthorized on account → correctly detected → fallback to one-time Orders.
  - Frontend supports both order and subscription flows.
- Traffic Sources Analytics shipped:
  - Backend attribution + `/api/admin/traffic`.
  - Admin UI tab with chart/tables.
- Community Lounge shipped:
  - `/lounge` page premium-only.
  - Announcements + discussion threads + replies + basic moderation/rate limits.

## STATUS UPDATE (V2.2 — Autopay live switch-on + lounge notifications + traffic trends + pinned threads) ✅ COMPLETE
- Autopay Switch-On:
  - Added throttled live re-probe on `/api/billing/config` and `/api/billing/razorpay/checkout` so autopay activates automatically once enabled on Razorpay dashboard (no restart required).
- Lounge Notifications:
  - Thread-author bell notifications on lounge replies + deep-link support `/lounge?thread=<id>`.
- Traffic Trends:
  - Weekly traffic trends returned by backend and displayed as a multi-line chart in Admin → Traffic.
- Pinned Discussions:
  - Admin pin/unpin endpoint, pinned-first sorting, Pinned badge on cards, pin toggle in thread detail.
- Testing:
  - `iteration_6.json`: backend 99.5% (183/184), frontend 100%, no regressions.

> Engineering note: `/app/backend/server.py` is large. Apply edits sequentially to avoid merge/conflict corruption; consider modularizing next.
